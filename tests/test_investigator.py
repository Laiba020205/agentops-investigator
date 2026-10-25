
from app.agents.investigator import investigate_trace
from app.agents.execution_agent import run_demo_agent


def test_detects_tool_timeout():
    run = run_demo_agent(
        order_id="ORD-101",
        simulate_timeout=True,
    )

    diagnosis = investigate_trace(run["trace"])

    assert run["status"] == "failure"
    assert diagnosis["root_cause"] == "tool_timeout"
    assert diagnosis["evidence"]
    assert diagnosis["evidence"][0]["sequence"] in {
        event["sequence"] for event in run["trace"]
    }


def test_detects_missing_order_id():
    trace = [
        {
            "sequence": 3,
            "event_type": "error",
            "status": "failure",
            "output_data": {
                "error": "order_id is required"
            },
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "missing_required_argument"
    assert result["evidence"][0]["sequence"] == 3
    assert "Validate required arguments" in result["recommendation"]


def test_handles_unknown_failure():
    trace = [
        {
            "sequence": 2,
            "event_type": "error",
            "status": "failure",
            "output_data": {
                "error": "Unexpected CRM response format"
            },
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unknown_failure"
    assert len(result["evidence"]) == 1


def test_handles_trace_without_failure():
    result = investigate_trace([
        {
            "sequence": 1,
            "event_type": "agent_start",
            "status": "success",
            "output_data": {},
        }
    ])

    assert result["root_cause"] == "no_failure_detected"


def test_handles_empty_trace():
    result = investigate_trace([])

    assert result["root_cause"] == "no_failure_detected"
    assert result["evidence"] == []


def test_detects_malformed_tool_result():
    trace = [
        {
            "sequence": 4,
            "event_type": "tool_result",
            "name": "get_order_status",
            "status": "success",
            "output_data": {
                "order_id": "ORD-101"
            },
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "malformed_tool_response"
    assert result["evidence"][0]["sequence"] == 4


def test_detects_conflicting_evidence():
    trace = [
        {
            "sequence": 4,
            "event_type": "error",
            "name": "order_status_validation",
            "status": "failure",
            "output_data": {
                "error": "Conflicting status evidence",
                "reported_status": "Delivered",
                "tool_status": "Shipped",
            },
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unsupported_answer"
    assert result["evidence"][0]["sequence"] == 4


def test_detects_unsupported_final_answer():
    trace = [
        {
            "sequence": 4,
            "event_type": "tool_result",
            "name": "get_order_status",
            "status": "success",
            "output_data": {
                "order_id": "ORD-101",
                "status": "Shipped",
            },
        },
        {
            "sequence": 5,
            "event_type": "agent_finish",
            "status": "success",
            "output_data": {
                "answer_status": "Delivered",
            },
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unsupported_answer"
    assert result["evidence"][0]["sequence"] == 5


def test_detects_repeated_identical_tool_calls():
    trace = [
        {
            "sequence": 1,
            "event_type": "tool_call",
            "name": "get_order_status",
            "input_data": {"order_id": "ORD-101"},
        },
        {
            "sequence": 2,
            "event_type": "tool_call",
            "name": "get_order_status",
            "input_data": {"order_id": "ORD-101"},
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "repeated_tool_call"
    assert result["evidence"][0]["sequence"] == 2


def test_does_not_flag_retry_after_recorded_error():
    trace = [
        {
            "sequence": 1,
            "event_type": "tool_call",
            "name": "get_order_status",
            "input_data": {"order_id": "ORD-101"},
        },
        {
            "sequence": 2,
            "event_type": "error",
            "status": "failure",
            "output_data": {"error": "Tool timed out"},
        },
        {
            "sequence": 3,
            "event_type": "tool_call",
            "name": "get_order_status",
            "input_data": {"order_id": "ORD-101"},
        },
        {
            "sequence": 4,
            "event_type": "tool_result",
            "name": "get_order_status",
            "status": "success",
            "output_data": {
                "order_id": "ORD-101",
                "status": "Shipped",
            },
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "tool_timeout"


def test_detects_malformed_response_even_when_timeout_comes_first():
    trace = [
        {
            "sequence": 1,
            "event_type": "error",
            "status": "failure",
            "output_data": {"error": "Tool timed out"},
        },
        {
            "sequence": 2,
            "event_type": "error",
            "status": "failure",
            "output_data": {
                "error": "Malformed tool response: missing status"
            },
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "malformed_tool_response"
    assert result["evidence"][0]["sequence"] == 2


def test_detects_unsupported_answer_when_events_are_out_of_order():
    trace = [
        {
            "sequence": 5,
            "event_type": "agent_finish",
            "status": "success",
            "output_data": {"answer_status": "Delivered"},
        },
        {
            "sequence": 3,
            "event_type": "tool_result",
            "name": "get_order_status",
            "status": "success",
            "output_data": {
                "order_id": "ORD-101",
                "status": "Shipped",
            },
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unsupported_answer"


def test_handles_none_output_data():
    trace = [
        {
            "sequence": 1,
            "event_type": "error",
            "status": "failure",
            "output_data": None,
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unknown_failure"


def test_detects_missing_fields_in_tool_result():
    trace = [
        {
            "sequence": 7,
            "event_type": "tool_result",
            "name": "get_order_status",
            "status": "success",
            "output_data": None,
        }
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "malformed_tool_response"
    assert result["evidence"][0]["sequence"] == 7


def test_detects_conflicting_evidence_with_successful_finish():
    trace = [
        {
            "sequence": 4,
            "event_type": "error",
            "name": "order_status_validation",
            "status": "failure",
            "output_data": {
                "error": "Conflicting status evidence",
            },
        },
        {
            "sequence": 5,
            "event_type": "agent_finish",
            "status": "success",
            "output_data": {"answer_status": "Delivered"},
        },
    ]

    result = investigate_trace(trace)

    assert result["root_cause"] == "unsupported_answer"
    assert result["evidence"][0]["sequence"] == 4
