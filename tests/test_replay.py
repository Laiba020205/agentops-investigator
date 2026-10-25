
from app.agents.execution_agent import run_demo_agent
from app.agents.replay import compare_runs, replay_with_order_id


def test_corrected_order_id_succeeds():
    result = run_demo_agent(order_id="ORD-101")

    assert result["status"] == "success"
    assert result["answer"]["status"] == "Shipped"


def test_replay_fixes_missing_argument():
    baseline = run_demo_agent()
    result = replay_with_order_id("ORD-101", baseline)

    assert result["comparison"]["failure_fixed"] is True
    assert result["comparison"]["baseline_status"] == "failure"
    assert result["comparison"]["candidate_status"] == "success"


def test_invalid_order_does_not_count_as_fix():
    baseline = run_demo_agent()
    result = replay_with_order_id("ORD-999", baseline)

    assert result["comparison"]["failure_fixed"] is False
