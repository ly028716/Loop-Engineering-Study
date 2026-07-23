"""Deterministic single-parameter sensitivity analysis for loop policies."""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached

from experiments.adaptive_strategy import (
    AdaptivePolicy,
    ErrorAwarePolicy,
    FixedPolicy,
    MemoryAwarePolicy,
    RecoveryAwareEvaluator,
)

STRATEGIES = ("fixed", "error_aware", "memory_aware", "adaptive")
BASELINE = {"goal_distance": 6, "failure_attempt": 2, "step_budget": 8}
PARAMETER_VALUES = {
    "goal_distance": (4, 6, 8),
    "failure_attempt": (1, 2, 3),
    "step_budget": (3, 5, 8),
}


class FailOnAttemptAction(Action):
    """Inject exactly one failed action at the configured attempt number."""

    def __init__(self, failure_attempt: int) -> None:
        self._failure_attempt = failure_attempt
        self._attempts = 0
        self._numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        self._attempts += 1
        if self._attempts == self._failure_attempt:
            return ActionResult(
                state=state.with_value(state.value, injected_failure=True),
                success=False,
                cost=0.0,
            )
        return self._numeric_action.apply(state, decision)


def _policy_for(strategy: str) -> Policy:
    policies: dict[str, type[Policy]] = {
        "fixed": FixedPolicy,
        "error_aware": ErrorAwarePolicy,
        "memory_aware": MemoryAwarePolicy,
        "adaptive": AdaptivePolicy,
    }
    try:
        return policies[strategy]()
    except KeyError as error:
        raise ValueError(f"Unknown sensitivity strategy: {strategy}") from error


def _configurations() -> list[dict[str, object]]:
    return [
        {
            "parameter_family": family,
            "parameter_value": value,
            "parameters": {**BASELINE, family: value},
            "baseline": dict(BASELINE),
            "runs": [],
            "artifact_paths": [],
            "ranking": [],
        }
        for family, values in PARAMETER_VALUES.items()
        for value in values
    ]


def _recovery_count(trace: LoopTrace) -> int:
    return sum(
        event.phase == "DECIDE"
        and event.payload["parameters"].get("mode_code") == 3.0
        for event in trace.events
    )


def _run_case(
    root: Path, configuration: dict[str, object], strategy: str
) -> dict[str, object]:
    parameters = configuration["parameters"]
    if not isinstance(parameters, dict):
        raise TypeError("Sensitivity parameters must be a dictionary")

    goal_distance = int(parameters["goal_distance"])
    failure_attempt = int(parameters["failure_attempt"])
    step_budget = int(parameters["step_budget"])
    runner = LoopRunner(
        policy=_policy_for(strategy),
        action=FailOnAttemptAction(failure_attempt),
        evaluator=RecoveryAwareEvaluator(),
        stop_conditions=[SuccessReached(), MaxSteps(step_budget)],
    )
    trace = runner.run(LoopState(step=0, value=0.0, goal=float(goal_distance)))
    report = MetricReport.from_trace(trace)
    family = str(configuration["parameter_family"])
    value = int(configuration["parameter_value"])
    artifact_path = save_run_artifact(
        root / f"{family}-{value}--{strategy}.json", trace, report
    )
    return {
        "strategy": strategy,
        "success": report.success,
        "steps": report.steps,
        "final_score": report.final_score,
        "failure_count": sum(
            event.phase == "ACT" and event.payload["success"] is False
            for event in trace.events
        ),
        "recovery_count": _recovery_count(trace),
        "budget_respected": report.steps <= step_budget,
        "artifact_path": str(artifact_path),
    }


def _score_and_rank(runs: list[dict[str, object]]) -> list[dict[str, object]]:
    successful_steps = [int(item["steps"]) for item in runs if item["success"]]
    best_steps = min(successful_steps) if successful_steps else None
    for item in runs:
        success = bool(item["success"])
        success_score = 50.0 if success else 0.0
        efficiency_score = (
            25.0 * best_steps / int(item["steps"])
            if success and best_steps is not None
            else 0.0
        )
        recovery_score = (
            15.0 if success and int(item["recovery_count"]) >= 1 else 0.0
        )
        budget_score = 10.0 if item["budget_respected"] else 0.0
        item["total_score"] = (
            success_score + efficiency_score + recovery_score + budget_score
        )

    ranking = sorted(
        runs,
        key=lambda item: (
            -float(item["total_score"]),
            int(item["steps"]),
            str(item["strategy"]),
        ),
    )
    for rank, item in enumerate(ranking, start=1):
        item["rank"] = rank
    return ranking


def _flip_analysis(configurations: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    analysis: dict[str, dict[str, object]] = {}
    for family in PARAMETER_VALUES:
        ordered = sorted(
            (
                item
                for item in configurations
                if item["parameter_family"] == family
            ),
            key=lambda item: int(item["parameter_value"]),
        )
        flips: list[dict[str, object]] = []
        for before, after in zip(ordered, ordered[1:]):
            before_order = {
                str(item["strategy"]): int(item["rank"])
                for item in before["ranking"]
            }
            after_order = {
                str(item["strategy"]): int(item["rank"])
                for item in after["ranking"]
            }
            for left, right in combinations(STRATEGIES, 2):
                if (before_order[left] < before_order[right]) != (
                    after_order[left] < after_order[right]
                ):
                    flips.append(
                        {
                            "from_value": before["parameter_value"],
                            "to_value": after["parameter_value"],
                            "pair": [left, right],
                        }
                    )
        analysis[family] = {"flips": flips, "no_flip": not flips}
    return analysis


def run_sensitivity(
    output_dir: str | Path = ".loop/runs/sensitivity-analysis",
) -> dict[str, object]:
    """Run every one-parameter configuration and identify ranking flips."""

    root = Path(output_dir).resolve()
    configurations = _configurations()
    all_runs: list[dict[str, object]] = []
    for configuration in configurations:
        configuration_runs = [
            _run_case(root, configuration, strategy) for strategy in STRATEGIES
        ]
        configuration["runs"] = configuration_runs
        configuration["artifact_paths"] = [
            item["artifact_path"] for item in configuration_runs
        ]
        configuration["ranking"] = _score_and_rank(configuration_runs)
        all_runs.extend(configuration_runs)
    return {
        "configurations": configurations,
        "runs": all_runs,
        "flip_analysis": _flip_analysis(configurations),
    }


def main() -> None:
    """Print the deterministic sensitivity analysis as JSON."""

    print(json.dumps(run_sensitivity(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
