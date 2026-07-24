import json
from pathlib import Path

from experiments.multi_objective_evaluation import run_multi_objective_evaluation


def test_evaluation_reuses_benchmark_and_persists_stable_report(tmp_path: Path) -> None:
    result = run_multi_objective_evaluation(tmp_path)

    assert len(result["benchmark_runs"]) == 20
    assert [item["strategy"] for item in result["points"]] == [
        "fixed",
        "error_aware",
        "memory_aware",
        "adaptive",
    ]
    assert set(result["dominated_by"]).issubset(
        {item["strategy"] for item in result["points"]}
    )
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == result
