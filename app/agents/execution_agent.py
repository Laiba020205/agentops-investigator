
from app.tools.mock_crm import get_order_status
from app.tracing.collector import collector


def run_demo_agent(
    order_id: str | None = None,
    simulate_timeout: bool = False,
    simulate_repeated_tool_call: bool = False,
    simulate_malformed_response: bool = False,
    simulate_unsupported_answer: bool = False,
    simulate_conflicting_evidence: bool = False,
    simulate_multiple_failures: bool = False,
    simulate_misleading_answer: bool = False,
) -> dict:
    run_id = collector.start_run()

    collector.record(
        run_id=run_id,
        event_type="agent_start",
        name="order_status_agent",
        input_data={"task": "Find the customer's order status"},
    )

    tool_input = {}
    if order_id is not None:
        tool_input["order_id"] = order_id

    status = "success"
    answer = None
    result = None

    collector.record(
        run_id=run_id,
        event_type="tool_call",
        name="get_order_status",
        input_data=tool_input,
        status="running",
    )

    try:
        if "order_id" not in tool_input:
            raise ValueError("order_id is required")

        if simulate_timeout:
            raise TimeoutError("CRM tool request timed out")

        if simulate_multiple_failures:
            # First attempt: timeout.
            collector.record(
                run_id=run_id,
                event_type="error",
                name="get_order_status",
                input_data=tool_input,
                output_data={"error": "CRM tool request timed out"},
                status="failure",
            )

            # Second attempt: tool returns an invalid payload.
            collector.record(
                run_id=run_id,
                event_type="tool_call",
                name="get_order_status",
                input_data=tool_input,
                status="running",
            )

            result = {
                "unexpected_payload": {
                    "order_id": order_id,
                    "status": "Shipped",
                },
                "invalid_format": True,
            }

            collector.record(
                run_id=run_id,
                event_type="tool_result",
                name="get_order_status",
                output_data=result,
                status="success",
            )

            raise ValueError(
                "Malformed tool response after timeout retry"
            )

        result = get_order_status(**tool_input)

        if simulate_repeated_tool_call:
            collector.record(
                run_id=run_id,
                event_type="tool_call",
                name="get_order_status",
                input_data=tool_input,
                status="running",
            )
            result = get_order_status(**tool_input)

        if simulate_malformed_response:
            result = {
                "unexpected_payload": result,
                "invalid_format": True,
            }

        collector.record(
            run_id=run_id,
            event_type="tool_result",
            name="get_order_status",
            output_data=result,
        )

        if simulate_malformed_response:
            raise ValueError(
                "Malformed tool response: missing order_id or status"
            )

        if simulate_conflicting_evidence:
            # Add an explicit contradictory event to the trace.
            collector.record(
                run_id=run_id,
                event_type="error",
                name="order_status_validation",
                input_data={"order_id": order_id},
                output_data={
                    "error": "Conflicting status evidence",
                    "reported_status": "Delivered",
                    "tool_status": result["status"],
                },
                status="failure",
            )

        if simulate_unsupported_answer or simulate_misleading_answer:
            # Intentionally contradict the CRM result.
            answer = {
                "order_id": order_id,
                "status": "Delivered",
            }
        else:
            answer = result

    except (TypeError, ValueError, TimeoutError) as exc:
        error_message = str(exc)

        collector.record(
            run_id=run_id,
            event_type="error",
            name="get_order_status",
            input_data=tool_input,
            output_data={"error": error_message},
            status="failure",
        )

        status = "failure"
        answer = {"error": error_message}

    collector.record(
        run_id=run_id,
        event_type="agent_finish",
        name="order_status_agent",
        output_data={
            "status": status,
            "answer_status": (
                answer.get("status")
                if isinstance(answer, dict)
                else None
            ),
        },
        status=status,
    )

    return {
        "run_id": run_id,
        "status": status,
        "answer": answer,
        "trace": [
            event.model_dump(mode="json")
            for event in collector.get_events(run_id)
        ],
    }
