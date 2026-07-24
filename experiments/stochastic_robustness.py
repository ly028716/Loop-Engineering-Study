"""Reproducible random-failure and noisy-execution robustness experiment."""

from __future__ import annotations

import random
from pathlib import Path

from loop_engineering.actions import Action, ActionResult
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState
from loop_engineering.policies import Decision
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached

from experiments.adaptive_strategy import (
    AdaptivePolicy,
    ErrorAwarePolicy,
    FixedPolicy,
    MemoryAwarePolicy,
)

STRATEGIES = ("fixed", "error_aware", "memory_aware", "adaptive")
SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
LEVELS = (("low", 0.05, 0.10), ("medium", 0.15, 0.30), ("high", 0.30, 0.60))


class StochasticAction(Action):
    """Apply an increment with independent random failure and bounded noise."""

    def __init__(
        self, failure_rate: float, noise_amplitude: float, rng: random.Random
    ) -> None:
        if not 0.0 <= failure_rate <= 1.0:
            raise ValueError("failure_rate must be between 0 and 1.")
        if noise_amplitude < 0.0:
            raise ValueError("noise_amplitude must be non-negative.")
        self._failure_rate = failure_rate
        self._noise_amplitude = noise_amplitude
        self._rng = rng

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if self._rng.random() < self._failure_rate:
            return ActionResult(
                state=state.with_value(state.value, stochastic_failure=True),
                success=False,
                cost=0.0,
            )
        amount = float(decision.parameters["amount"])
        actual_amount = amount + self._rng.uniform(
            -self._noise_amplitude, self._noise_amplitude
        )
        return ActionResult(
            state=state.with_value(state.value + actual_amount),
            success=True,
            cost=abs(actual_amount),
        )


def _policy_for(strategy: str):
    return {
        "fixed": FixedPolicy,
        "error_aware": ErrorAwarePolicy,
        "memory_aware": MemoryAwarePolicy,
        "adaptive": AdaptivePolicy,
    }[strategy]()


def _run(root: Path, level: str, failure_rate: float, noise: float, strategy: str, seed: int) -> dict[str, object]:
    trace = LoopRunner(
        policy=_policy_for(strategy),
        action=StochasticAction(failure_rate, noise, random.Random(seed)),
        evaluator=GoalEvaluator(tolerance=0.25),
        stop_conditions=[SuccessReached(), MaxSteps(8)],
    ).run(LoopState(step=0, value=0.0, goal=6.0))
    metrics = MetricReport.from_trace(trace)
    artifact = save_run_artifact(root / f"{level}--{strategy}--{seed}.json", trace, metrics)
    return {"level": level, "strategy": strategy, "seed": seed, "success": metrics.success, "cost": metrics.cost, "steps": metrics.steps, "final_score": metrics.final_score, "artifact_path": str(artifact)}


def _summary(level: str, strategy: str, runs: list[dict[str, object]]) -> dict[str, object]:
    costs = sorted(float(item["cost"]) for item in runs)
    steps = sorted(int(item["steps"]) for item in runs)
    index = 7
    return {"level": level, "strategy": strategy, "run_count": len(runs), "success_count": sum(bool(item["success"]) for item in runs), "success_rate": sum(bool(item["success"]) for item in runs) / len(runs), "mean_cost": sum(costs) / len(costs), "worst_cost": costs[-1], "cost_p90": costs[index], "mean_steps": sum(steps) / len(steps), "steps_p90": steps[index]}


def run_stochastic_robustness(output_dir: str | Path = ".loop/runs/stochastic-robustness") -> dict[str, object]:
    """Run the fixed stochastic matrix and persist every run artifact."""
    root = Path(output_dir).resolve()
    runs = [_run(root, level, rate, noise, strategy, seed) for level, rate, noise in LEVELS for strategy in STRATEGIES for seed in SEEDS]
    summaries = [_summary(level, strategy, [item for item in runs if item["level"] == level and item["strategy"] == strategy]) for level, _, _ in LEVELS for strategy in STRATEGIES]
    rankings = {level: sorted([item for item in summaries if item["level"] == level], key=lambda item: (-float(item["success_rate"]), float(item["cost_p90"]), float(item["mean_steps"]), STRATEGIES.index(str(item["strategy"])))) for level, _, _ in LEVELS}
    result = {"levels": [item[0] for item in LEVELS], "strategies": list(STRATEGIES), "runs": runs, "summaries": summaries, "rankings": rankings}
    import json
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
