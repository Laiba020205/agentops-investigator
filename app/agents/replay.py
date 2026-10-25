
from typing import Any

from app.agents.execution_agent import run_demo_agent


def compare_runs(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    baseline_success = baseline["status"] == "success"
    candidate_success = candidate["status"] == "success"

    fixed = not baseline_success and candidate_success

    return {
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "baseline_status": baseline["status"],
        "candidate_status": candidate["status"],
        "failure_fixed": fixed,
        "regression_detected": baseline_success and not candidate_success,
        "recommendation": (
            "Candidate fixed the baseline failure."
            if fixed
            else "Candidate did not demonstrate a fix."
        ),
    }


def replay_with_order_id(
    order_id: str,
    baseline: dict[str, Any],
) -> dict[str, Any]:
    candidate = run_demo_agent(order_id=order_id)

    return {
        "candidate": candidate,
        "comparison": compare_runs(baseline, candidate),
    }
