
from app.agents.execution_agent import run_demo_agent


def test_agent_captures_tool_failure():
    result = run_demo_agent()

    assert result["status"] == "failure"
    assert result["answer"]["error"] == "order_id is required"

    trace = result["trace"]

    assert len(trace) == 4
    assert trace[0]["event_type"] == "agent_start"
    assert trace[1]["event_type"] == "tool_call"
    assert trace[2]["event_type"] == "error"
    assert trace[3]["event_type"] == "agent_finish"
