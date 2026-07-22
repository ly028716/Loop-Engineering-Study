from pathlib import Path

from experiments.convergence_stopping import run_comparison
from loop_engineering.artifacts import load_run_artifact


def test_run_comparison_has_expected_stop_reasons(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)
    by_mode = {item["mode"]: item for item in results}

    assert by_mode["converging"]["success"] is True
    assert by_mode["stalled"]["stop_reason"] == "No progress for 3 evaluations"
    assert by_mode["oscillating"]["stop_reason"] == "Reached maximum steps: 6"
    assert all(Path(item["artifact_path"]).exists() for item in results)

    for item in results:
        trace, report = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        assert report.steps == item["steps"]
