from pathlib import Path

from experiments.benchmark_suite import run_benchmark
from loop_engineering.artifacts import load_run_artifact


def test_benchmark_runs_matrix_and_persists_artifacts(tmp_path: Path) -> None:
    result = run_benchmark(tmp_path)

    assert result["scenarios"] == [
        "steady_progress",
        "action_failure",
        "missing_feedback",
        "stalled_progress",
        "tight_budget",
    ]
    assert result["strategies"] == [
        "fixed",
        "error_aware",
        "memory_aware",
        "adaptive",
    ]
    assert len(result["runs"]) == 20
    assert all(Path(item["artifact_path"]).exists() for item in result["runs"])

    for item in result["runs"]:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"


def test_benchmark_scores_are_bounded_and_ranked(tmp_path: Path) -> None:
    result = run_benchmark(tmp_path)
    summaries = {item["strategy"]: item for item in result["summaries"]}
    ranking = result["ranking"]

    assert all(0.0 <= item["total_score"] <= 100.0 for item in summaries.values())
    assert ranking == sorted(
        ranking,
        key=lambda item: (
            -item["total_score"],
            item["average_success_steps"],
            item["strategy"],
        ),
    )
    assert summaries["adaptive"]["total_score"] > summaries["fixed"]["total_score"]
