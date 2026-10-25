
from benchmark.run_benchmark import run_benchmark


def test_benchmark_reports_all_scenarios():
    report = run_benchmark()

    assert report["total_scenarios"] == 11
    assert report["task_pass_rate"] == 1.0
    assert report["diagnostic_accuracy"] == 1.0
    assert report["overall_diagnostic_accuracy"] == 1.0
    assert report["evidence_support_rate"] == 1.0


def test_benchmark_has_no_unsupported_evidence():
    report = run_benchmark()

    assert all(
        result["evidence_supported"]
        for result in report["results"]
    )


def test_benchmark_scenarios_are_unique():
    report = run_benchmark()

    scenario_names = [
        result["scenario"]
        for result in report["results"]
    ]

    assert len(scenario_names) == len(set(scenario_names))


def test_every_scenario_has_a_correct_diagnosis():
    report = run_benchmark()

    assert all(
        result["diagnosis_correct"]
        for result in report["results"]
    )


def test_benchmark_report_has_required_fields():
    report = run_benchmark()

    required_fields = {
        "total_scenarios",
        "task_pass_rate",
        "diagnostic_accuracy",
        "overall_diagnostic_accuracy",
        "evidence_support_rate",
        "results",
    }

    assert required_fields.issubset(report.keys())


def test_benchmark_metrics_are_valid_rates():
    report = run_benchmark()

    metric_names = [
        "task_pass_rate",
        "diagnostic_accuracy",
        "overall_diagnostic_accuracy",
        "evidence_support_rate",
    ]

    for metric in metric_names:
        assert 0.0 <= report[metric] <= 1.0


def test_each_result_has_required_fields():
    report = run_benchmark()

    required_fields = {
        "scenario",
        "diagnosis_correct",
        "evidence_supported",
    }

    for result in report["results"]:
        assert required_fields.issubset(result.keys())


def test_report_result_count_matches_total():
    report = run_benchmark()

    assert len(report["results"]) == report["total_scenarios"]
