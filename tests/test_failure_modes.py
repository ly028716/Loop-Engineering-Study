from pathlib import Path

from experiments.failure_modes import run_comparison
from loop_engineering.artifacts import load_run_artifact


def test_run_comparison_returns_all_failure_modes(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)

    assert [item["failure_mode"] for item in results] == [
        "action_failure",
        "evaluator_disagreement",
        "missing_feedback",
        "oscillation",
        "safety_limit",
    ]
    assert all(Path(item["artifact_path"]).exists() for item in results)


def test_failure_modes_have_expected_detection_and_stopping(tmp_path: Path) -> None:
    results = {item["failure_mode"]: item for item in run_comparison(tmp_path)}

    assert results["action_failure"]["success"] is True
    assert results["action_failure"]["recovery_attempts"] >= 1
    assert results["evaluator_disagreement"]["evidence_conflicts"] == 1
    assert results["missing_feedback"]["failure_count"] >= 1
    assert results["oscillation"]["stop_reason"] == "Reached maximum steps: 6"
    assert results["safety_limit"]["stop_reason"] == "Reached maximum steps: 3"

    for item in results.values():
        trace, report = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        assert report.steps == item["steps"]
