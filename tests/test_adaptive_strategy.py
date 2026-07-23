from pathlib import Path

from experiments.adaptive_strategy import run_comparison
from loop_engineering.artifacts import load_run_artifact


def test_adaptive_comparison_is_replayable_and_more_efficient(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)
    by_strategy = {item["strategy"]: item for item in results}

    assert [item["strategy"] for item in results] == [
        "fixed", "error_aware", "memory_aware", "adaptive"
    ]
    assert all(item["success"] is True for item in results)
    assert by_strategy["adaptive"]["steps"] < by_strategy["fixed"]["steps"]
    assert by_strategy["adaptive"]["steps"] <= 8
    assert by_strategy["adaptive"]["switch_count"] >= 1
    assert by_strategy["adaptive"]["recovery_count"] >= 1

    for item in results:
        trace, report = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        assert report.steps == item["steps"]


def test_adaptive_trace_records_recovery_mode_after_failure(tmp_path: Path) -> None:
    result = next(item for item in run_comparison(tmp_path) if item["strategy"] == "adaptive")
    trace, _ = load_run_artifact(result["artifact_path"])

    failed_action_index = next(
        index
        for index, event in enumerate(trace.events)
        if event.phase == "ACT" and event.payload["success"] is False
    )
    later_modes = [
        event.payload["parameters"].get("mode_code")
        for event in trace.events[failed_action_index + 1 :]
        if event.phase == "DECIDE"
    ]
    assert 3.0 in later_modes
