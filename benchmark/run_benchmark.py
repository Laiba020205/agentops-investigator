
import json
from pathlib import Path

from app.agents.execution_agent import run_demo_agent
from app.agents.investigator import investigate_trace


SCENARIOS = [
    {
        "name": "missing_order_id",
        "order_id": None,
        "expected_status": "failure",
        "expected_root_cause": "missing_required_argument",
    },
    {
        "name": "valid_order",
        "order_id": "ORD-101",
        "expected_status": "success",
        "expected_root_cause": "no_failure_detected",
    },
    {
        "name": "unknown_order",
        "order_id": "ORD-999",
        "expected_status": "failure",
        "expected_root_cause": "resource_not_found",
    },
    {
        "name": "second_valid_order",
        "order_id": "ORD-102",
        "expected_status": "success",
        "expected_root_cause": "no_failure_detected",
    },
    {
        "name": "tool_timeout",
        "order_id": "ORD-101",
        "simulate_timeout": True,
        "expected_status": "failure",
        "expected_root_cause": "tool_timeout",
    },
    {
        "name": "repeated_tool_call",
        "order_id": "ORD-101",
        "simulate_repeated_tool_call": True,
        "expected_status": "success",
        "expected_root_cause": "repeated_tool_call",
    },
    {
        "name": "malformed_tool_response",
        "order_id": "ORD-101",
        "simulate_malformed_response": True,
        "expected_status": "failure",
        "expected_root_cause": "malformed_tool_response",
    },
    {
        "name": "unsupported_answer",
        "order_id": "ORD-101",
        "simulate_unsupported_answer": True,
        "expected_status": "success",
        "expected_root_cause": "unsupported_answer",
    },
    {
        "name": "conflicting_evidence",
        "order_id": "ORD-101",
        "simulate_conflicting_evidence": True,
        "expected_status": "success",
        "expected_root_cause": "unsupported_answer",
    },
    {
        "name": "multiple_failures",
        "order_id": "ORD-101",
        "simulate_multiple_failures": True,
        "expected_status": "failure",
        "expected_root_cause": "malformed_tool_response",
    },
    {
        "name": "misleading_answer",
        "order_id": "ORD-101",
        "simulate_misleading_answer": True,
        "expected_status": "success",
        "expected_root_cause": "unsupported_answer",
    },
]


def run_benchmark() -> dict:
    results = []

    for scenario in SCENARIOS:
        run_options = {
            key: value
            for key, value in scenario.items()
            if key.startswith("simulate_")
        }

        run = run_demo_agent(
            order_id=scenario["order_id"],
            **run_options,
        )

        diagnosis = investigate_trace(run["trace"])

        task_passed = (
            run["status"] == scenario["expected_status"]
        )

        diagnosis_correct = (
            diagnosis["root_cause"]
            == scenario["expected_root_cause"]
        )

        event_sequences = {
            event["sequence"] for event in run["trace"]
        }

        evidence = diagnosis.get("evidence", [])

        evidence_supported = all(
            item.get("sequence") in event_sequences
            for item in evidence
        )

        results.append({
            "scenario": scenario["name"],
            "run_id": run["run_id"],
            "actual_status": run["status"],
            "expected_status": scenario["expected_status"],
            "task_passed": task_passed,
            "predicted_root_cause": diagnosis["root_cause"],
            "expected_root_cause": scenario["expected_root_cause"],
            "diagnosis_correct": diagnosis_correct,
            "evidence_supported": evidence_supported,
            "evidence": evidence,
            "recommendation": diagnosis.get("recommendation"),
        })

    total = len(results)

    failures = [
        result
        for result in results
        if result["expected_status"] == "failure"
    ]

    report = {
        "total_scenarios": total,
        "task_pass_rate": (
            sum(item["task_passed"] for item in results) / total
            if total else None
        ),
        "diagnostic_accuracy": (
            sum(item["diagnosis_correct"] for item in failures)
            / len(failures)
            if failures else None
        ),
        "evidence_support_rate": (
            sum(item["evidence_supported"] for item in results) / total
            if total else None
        ),
        "overall_diagnostic_accuracy": (
            sum(item["diagnosis_correct"] for item in results) / total
            if total else None
        ),
        "results": results,
    }

    output_path = (
        Path(__file__).resolve().parent / "benchmark_report.json"
    )

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report


if __name__ == "__main__":
    report = run_benchmark()

    print(json.dumps({
        key: value
        for key, value in report.items()
        if key != "results"
    }, indent=2))

    print("\nScenario results:")

    for result in report["results"]:
        print(
            f"{result['scenario']}: "
            f"task_passed={result['task_passed']}, "
            f"diagnosis_correct={result['diagnosis_correct']}, "
            f"evidence_supported={result['evidence_supported']}"
        )

    print("\nFull report saved to benchmark/benchmark_report.json")
