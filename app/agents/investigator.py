
from typing import Any


def investigate_trace(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze an execution trace and diagnose the most likely defect."""

    def diagnose(
        root_cause: str,
        confidence: float,
        event: dict[str, Any] | None,
        recommendation: str,
        error: str | None = None,
    ) -> dict[str, Any]:
        evidence = []

        if event is not None:
            output = event.get("output_data") or {}
            evidence.append({
                "sequence": event.get("sequence"),
                "event": event.get("event_type"),
                "error": error or output.get("error") or event.get("name"),
            })

        return {
            "root_cause": root_cause,
            "confidence": confidence,
            "evidence": evidence,
            "recommendation": recommendation,
        }

    # 1. Detect explicitly recorded malformed tool responses first.
    # A malformed response takes precedence over an earlier timeout
    # when both occur in the same execution.
    for event in trace:
        output = event.get("output_data") or {}
        message = str(output.get("error", "")).lower()

        if (
            event.get("event_type") == "error"
            and "malformed tool response" in message
        ):
            return diagnose(
                "malformed_tool_response",
                1.0,
                event,
                "Validate the response schema before consuming tool output. "
                "Record retry attempts and their outcomes separately.",
            )

    # Also validate the structure of recorded tool results.
    for event in trace:
        if (
            event.get("event_type") != "tool_result"
            or event.get("name") != "get_order_status"
        ):
            continue

        output = event.get("output_data")

        if not (
            isinstance(output, dict)
            and isinstance(output.get("order_id"), str)
            and isinstance(output.get("status"), str)
        ):
            return diagnose(
                "malformed_tool_response",
                1.0,
                event,
                "Validate required response fields and reject malformed "
                "tool output before producing a final answer.",
                "Tool result is missing a valid order_id or status",
            )

    # 2. Detect explicitly recorded contradictions.
    for event in trace:
        output = event.get("output_data") or {}

        if (
            event.get("name") == "order_status_validation"
            and output.get("error") == "Conflicting status evidence"
        ):
            return diagnose(
                "unsupported_answer",
                1.0,
                event,
                "Resolve conflicting status evidence before answering. "
                "Use the authoritative tool result or request verification.",
                "Conflicting status evidence was recorded",
            )

    # 3. Detect redundant repeated tool calls.
    # A retry after an intervening error can be justified.
    tool_calls = [
        (index, event)
        for index, event in enumerate(trace)
        if event.get("event_type") == "tool_call"
    ]

    for position, (index, event) in enumerate(tool_calls):
        inputs = event.get("input_data") or {}
        key = (
            event.get("name"),
            tuple(sorted((str(k), repr(v)) for k, v in inputs.items())),
        )

        for later_index, later_event in tool_calls[position + 1:]:
            later_inputs = later_event.get("input_data") or {}
            later_key = (
                later_event.get("name"),
                tuple(sorted(
                    (str(k), repr(v)) for k, v in later_inputs.items()
                )),
            )

            if later_key != key:
                continue

            between = trace[index + 1:later_index]

            # Do not classify a retry after a recorded error as redundant.
            if any(item.get("event_type") == "error" for item in between):
                continue

            return diagnose(
                "repeated_tool_call",
                0.98,
                later_event,
                "Avoid repeating identical tool calls unless a retry is "
                "necessary and explicitly justified.",
                "Repeated tool call with identical inputs",
            )

    # 4. Classify remaining errors.
    for event in trace:
        output = event.get("output_data") or {}
        message = str(output.get("error", "")).lower()

        if (
            event.get("event_type") != "error"
            and event.get("status") != "failure"
        ):
            continue

        if "order_id is required" in message:
            return diagnose(
                "missing_required_argument",
                1.0,
                event,
                "Validate required arguments before calling the tool. "
                "Ask for the order ID when it is missing.",
            )

        if "was not found" in message:
            return diagnose(
                "resource_not_found",
                1.0,
                event,
                "Verify the order ID and ask the user to confirm it.",
            )

        if "timed out" in message or "timeout" in message:
            return diagnose(
                "tool_timeout",
                1.0,
                event,
                "Set a timeout policy and retry safely when appropriate.",
            )

        return diagnose(
            "unknown_failure",
            0.0,
            event,
            "Inspect the failure trace and add a targeted diagnostic rule.",
        )

    # 5. Check whether the final answer contradicts tool evidence.
    tool_results = [
        event.get("output_data") or {}
        for event in trace
        if event.get("event_type") == "tool_result"
        and event.get("name") == "get_order_status"
    ]

    finish_events = [
        event
        for event in trace
        if event.get("event_type") == "agent_finish"
    ]

    if tool_results and finish_events:
        actual = tool_results[-1].get("status")
        finish_output = finish_events[-1].get("output_data") or {}
        claimed = finish_output.get("answer_status")

        if (
            actual is not None
            and claimed is not None
            and str(actual).casefold() != str(claimed).casefold()
        ):
            return diagnose(
                "unsupported_answer",
                0.95,
                finish_events[-1],
                "Ground the final answer in the tool result and verify "
                "that its claims match the recorded evidence.",
                f"Answer claimed {claimed!r}; tool returned {actual!r}",
            )

    # 6. Successful execution: cite the successful tool result as evidence.
    successful_result = next(
        (
            event
            for event in reversed(trace)
            if (
                event.get("event_type") == "tool_result"
                and event.get("name") == "get_order_status"
                and event.get("status") != "failure"
                and isinstance(event.get("output_data"), dict)
                and isinstance(
                    event["output_data"].get("order_id"), str
                )
                and isinstance(
                    event["output_data"].get("status"), str
                )
            )
        ),
        None,
    )

    if successful_result is not None:
        return diagnose(
            "no_failure_detected",
            1.0,
            successful_result,
            "The tool execution completed successfully. No failure was "
            "detected; use the recorded tool result as the source of truth.",
            "Successful tool result supports the execution outcome",
        )

    # Fallback for traces with no identifiable successful tool result.
    return {
        "root_cause": "no_failure_detected",
        "confidence": 1.0,
        "evidence": [],
        "recommendation": "No recorded failure was found.",
    }
