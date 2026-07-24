"""Pareto analysis over the deterministic loop-engineering benchmark."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.benchmark_suite import STRATEGIES, run_benchmark
from loop_engineering.artifacts import load_run_artifact
from loop_engineering.multi_objective import ObjectivePoint, dominated_by, pareto_front

OBJECTIVES = {
    "success_rate": "maximize",
    "total_cost": "minimize",
    "average_success_steps": "minimize",
}


def _point_for(strategy: str, runs: list[dict[str, object]]) -> ObjectivePoint:
    strategy_runs = [item for item in runs if item["strategy"] == strategy]
    successful = [item for item in strategy_runs if item["success"]]
    total_cost = sum(
        load_run_artifact(str(item["artifact_path"]))[1].cost
        for item in strategy_runs
    )
    average_success_steps = (
        sum(int(item["steps"]) for item in successful) / len(successful)
        if successful
        else None
    )
    return ObjectivePoint(
        strategy=strategy,
        success_rate=len(successful) / len(strategy_runs),
        total_cost=total_cost,
        average_success_steps=average_success_steps,
    )


def run_multi_objective_evaluation(
    output_dir: str | Path = ".loop/runs/multi-objective-evaluation",
) -> dict[str, object]:
    """Evaluate benchmark strategies without collapsing objectives into weights."""

    root = Path(output_dir).resolve()
    benchmark = run_benchmark(root / "benchmark-suite")
    runs = list(benchmark["runs"])
    points = tuple(_point_for(strategy, runs) for strategy in STRATEGIES)
    payload = {
        "objectives": OBJECTIVES,
        "points": [asdict(point) for point in points],
        "pareto_front": [asdict(point) for point in pareto_front(points)],
        "dominated_by": dominated_by(points),
        "benchmark_runs": runs,
    }
    root.mkdir(parents=True, exist_ok=True)
    report_path = root / "report.json"
    report_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    """Run the evaluation and print its report."""

    print(json.dumps(run_multi_objective_evaluation(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
