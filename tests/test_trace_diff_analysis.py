import json
from pathlib import Path

from experiments.trace_diff_analysis import run_trace_diff_analysis


def test_trace_diff_analysis_compares_each_repair_case(tmp_path: Path) -> None:
    results = run_trace_diff_analysis(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure",
        "stalled_progress",
        "tight_budget",
    ]
    assert all(item["repair_succeeded"] is True for item in results)
    assert all(item["comparison"]["first_difference"] is not None for item in results)
    assert all(item["comparison"]["identical"] is False for item in results)
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report == results


def test_trace_diff_analysis_keeps_case_order_stable(tmp_path: Path) -> None:
    first = run_trace_diff_analysis(tmp_path / "first")
    second = run_trace_diff_analysis(tmp_path / "second")

    assert [item["case"] for item in first] == [item["case"] for item in second]
    assert [item["comparison"]["first_difference"] for item in first] == [
        item["comparison"]["first_difference"] for item in second
    ]
