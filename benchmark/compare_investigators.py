
import json
import time
from pathlib import Path

from app.agents.execution_agent import run_demo_agent
from app.agents.investigator import investigate_trace
from app.agents.llm_investigator import investigate_with_gemini


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


def get_field(obj, field, default=None):
    """Read a field from either a dictionary or a Pydantic model."""
    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def get_root_cause(diagnosis):
    return get_field(diagnosis, "root_cause")


def validate_evidence(diagnosis, trace):
    """Validate cited event sequence numbers against the trace."""
    evidence = get_field(diagnosis, "evidence", []) or []

    if not evidence:
        return False

    trace_sequences = {
        get_field(event, "sequence")
        for event in trace
    }

    cited_sequences = [
        get_field(item, "sequence")
        for item in evidence
    ]

    return (
        all(sequence is not None for sequence in cited_sequences)
        and all(sequence in trace_sequences for sequence in cited_sequences)
    )


def run_investigator(investigator, trace):
    start = time.perf_counter()
    diagnosis = investigator(trace)
    latency_ms = (time.perf_counter() - start) * 1000

    return diagnosis, latency_ms


def main():
    results = []
    total = len(SCENARIOS)

    task_passed_count = 0
    rule_correct_count = 0
    rule_evidence_valid_count = 0
    gemini_correct_count = 0
    gemini_successful_calls = 0
    gemini_failed_calls = 0
    gemini_evidence_valid_count = 0

    rule_latencies = []
    gemini_latencies = []

    for scenario in SCENARIOS:
        print(f"\nRunning scenario: {scenario['name']}")

        simulation_options = {
            key: value
            for key, value in scenario.items()
            if key.startswith("simulate_")
        }

        execution = run_demo_agent(
            order_id=scenario["order_id"],
            **simulation_options,
        )

        trace = execution["trace"]
        actual_status = execution["status"]
        expected_cause = scenario["expected_root_cause"]

        task_passed = actual_status == scenario["expected_status"]
        task_passed_count += int(task_passed)

        # Rule-based investigator
        rule_diagnosis, rule_latency_ms = run_investigator(
            investigate_trace, trace
        )

        rule_cause = get_root_cause(rule_diagnosis)
        rule_correct = rule_cause == expected_cause
        rule_evidence_valid = validate_evidence(rule_diagnosis, trace)

        rule_correct_count += int(rule_correct)
        rule_evidence_valid_count += int(rule_evidence_valid)
        rule_latencies.append(rule_latency_ms)

        # Gemini investigator
        gemini_cause = None
        gemini_correct = False
        gemini_evidence_valid = False
        gemini_latency_ms = None
        gemini_error = None

        try:
            gemini_diagnosis, gemini_latency_ms = run_investigator(
                investigate_with_gemini, trace
            )

            gemini_cause = get_root_cause(gemini_diagnosis)
            gemini_correct = gemini_cause == expected_cause
            gemini_evidence_valid = validate_evidence(
                gemini_diagnosis, trace
            )

            gemini_successful_calls += 1
            gemini_correct_count += int(gemini_correct)
            gemini_evidence_valid_count += int(gemini_evidence_valid)
            gemini_latencies.append(gemini_latency_ms)

        except Exception as exc:
            gemini_failed_calls += 1
            gemini_error = f"{type(exc).__name__}: {exc}"

        print(f"  Expected: {expected_cause}")
        print(f"  Rule-based: {rule_cause} (correct={rule_correct})")
        print(f"  Rule evidence valid: {rule_evidence_valid}")

        if gemini_error is None:
            print(f"  Gemini: {gemini_cause} (correct={gemini_correct})")
            print(f"  Gemini evidence valid: {gemini_evidence_valid}")
            print(f"  Gemini latency: {gemini_latency_ms:.2f} ms")
        else:
            print(f"  Gemini failed: {gemini_error}")

        results.append({
            "scenario": scenario["name"],
            "expected_status": scenario["expected_status"],
            "actual_status": actual_status,
            "task_passed": task_passed,
            "expected_root_cause": expected_cause,
            "rule_based_root_cause": rule_cause,
            "rule_based_correct": rule_correct,
            "rule_based_evidence_valid": rule_evidence_valid,
            "rule_based_latency_ms": round(rule_latency_ms, 2),
            "gemini_root_cause": gemini_cause,
            "gemini_correct": gemini_correct,
            "gemini_evidence_valid": gemini_evidence_valid,
            "gemini_latency_ms": (
                round(gemini_latency_ms, 2)
                if gemini_latency_ms is not None
                else None
            ),
            "gemini_error": gemini_error,
        })

    report = {
        "total_scenarios": total,
        "task_pass_rate": round(task_passed_count / total, 4),
        "rule_based_accuracy": round(rule_correct_count / total, 4),
        "rule_based_evidence_validity": round(
            rule_evidence_valid_count / total, 4
        ),
        "gemini_successful_calls": gemini_successful_calls,
        "gemini_failed_calls": gemini_failed_calls,
        "gemini_call_success_rate": round(
            gemini_successful_calls / total, 4
        ),
        # Failed calls count as incorrect in this all-scenario metric.
        "gemini_accuracy": round(gemini_correct_count / total, 4),
        "gemini_accuracy_on_successful_calls": (
            round(gemini_correct_count / gemini_successful_calls, 4)
            if gemini_successful_calls else None
        ),
        "gemini_evidence_validity": (
            round(
                gemini_evidence_valid_count / gemini_successful_calls, 4
            )
            if gemini_successful_calls else None
        ),
        "average_rule_latency_ms": (
            round(sum(rule_latencies) / len(rule_latencies), 2)
            if rule_latencies else None
        ),
        "average_gemini_latency_ms": (
            round(sum(gemini_latencies) / len(gemini_latencies), 2)
            if gemini_latencies else None
        ),
        "results": results,
    }

    report_path = Path(__file__).resolve().with_name(
        "compare_report.json"
    )

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== Investigator Comparison ===")
    print(json.dumps({
        key: value
        for key, value in report.items()
        if key != "results"
    }, indent=2))

    print(f"\nFull report saved to {report_path}")


if __name__ == "__main__":
    main()
