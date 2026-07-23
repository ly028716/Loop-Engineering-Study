"""Deterministic matrix benchmark for Loop Engineering policies."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached

from experiments.adaptive_strategy import (
    AdaptivePolicy,
    ErrorAwarePolicy,
    FailOnSecondAction,
    FixedPolicy,
    MemoryAwarePolicy,
    RecoveryAwareEvaluator,
)

STRATEGIES = ("fixed", "error_aware", "memory_aware", "adaptive")
SCENARIOS = (
    "steady_progress",
    "action_failure",
    "missing_feedback",
    "stalled_progress",
    "tight_budget",
)
RECOVERY_SCENARIOS = frozenset({"action_failure", "missing_feedback"})


class StalledAction(Action):
    """Record successful actions that intentionally leave the value unchanged."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        del decision
        return ActionResult(state=state.with_value(state.value), success=True, cost=0.0)


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
        raise ValueError(f"Unknown benchmark strategy: {strategy}") from error


def build_scenario(scenario: str, strategy: str) -> tuple[LoopRunner, LoopState, int]:
    """Build one isolated deterministic scenario for one named strategy."""

    policy = _policy_for(strategy)
    goal = 6.0
    budget = 8
    action: Action = NumericAction()
    evaluator = RecoveryAwareEvaluator()

    if scenario == "action_failure":
        action = FailOnSecondAction()
    elif scenario == "missing_feedback":
        action = FailOnSecondAction()
        evaluator = GoalEvaluator(tolerance=0.0)
    elif scenario == "stalled_progress":
        action = StalledAction()
    elif scenario == "tight_budget":
        budget = 3
    elif scenario != "steady_progress":
        raise ValueError(f"Unknown benchmark scenario: {scenario}")

    return (
        LoopRunner(
            policy=policy,
            action=action,
            evaluator=evaluator,
            stop_conditions=[SuccessReached(), MaxSteps(budget)],
        ),
        LoopState(step=0, value=0.0, goal=goal),
        budget,
    )


def _recovery_count(trace: LoopTrace) -> int:
    return sum(
        event.phase == "DECIDE"
        and event.payload["parameters"].get("mode_code") == 3.0
        for event in trace.events
    )


def _run_case(root: Path, scenario: str, strategy: str) -> dict[str, object]:
    runner, initial_state, budget = build_scenario(scenario, strategy)
    trace = runner.run(initial_state)
    report = MetricReport.from_trace(trace)
    artifact_path = save_run_artifact(
        root / f"{scenario}--{strategy}.json", trace, report
    )
    return {
        "strategy": strategy,
        "scenario": scenario,
        "success": report.success,
        "status": trace.final_state.status if trace.final_state else "RUNNING",
        "steps": report.steps,
        "final_score": report.final_score,
        "failure_count": sum(
            event.phase == "ACT" and event.payload["success"] is False
            for event in trace.events
        ),
        "recovery_count": _recovery_count(trace),
        "budget_respected": report.steps <= budget,
        "artifact_path": str(artifact_path),
    }


def _efficiency_score(strategy: str, runs: list[dict[str, object]]) -> float:
    score = 0.0
    for scenario in SCENARIOS:
        scenario_runs = [item for item in runs if item["scenario"] == scenario]
        successful_steps = [
            int(item["steps"]) for item in scenario_runs if item["success"]
        ]
        strategy_run = next(
            item
            for item in scenario_runs
            if item["strategy"] == strategy
        )
        if successful_steps and strategy_run["success"]:
            score += 25.0 * min(successful_steps) / int(strategy_run["steps"])
    return score / len(SCENARIOS)


def _summarize(strategy: str, runs: list[dict[str, object]]) -> dict[str, object]:
    strategy_runs = [item for item in runs if item["strategy"] == strategy]
    successful = [item for item in strategy_runs if item["success"]]
    recovery_runs = [
        item for item in strategy_runs if item["scenario"] in RECOVERY_SCENARIOS
    ]
    success_score = 50.0 * len(successful) / len(SCENARIOS)
    recovery_score = 15.0 * sum(
        item["success"] and int(item["recovery_count"]) >= 1
        for item in recovery_runs
    ) / len(RECOVERY_SCENARIOS)
    budget_score = 10.0 * sum(
        bool(item["budget_respected"]) for item in strategy_runs
    ) / len(SCENARIOS)
    efficiency_score = _efficiency_score(strategy, runs)
    average_success_steps = (
        sum(int(item["steps"]) for item in successful) / len(successful)
        if successful
        else float("inf")
    )
    return {
        "strategy": strategy,
        "success_rate": len(successful) / len(SCENARIOS),
        "average_success_steps": average_success_steps,
        "recovery_rate": sum(
            item["success"] and int(item["recovery_count"]) >= 1
            for item in recovery_runs
        ) / len(RECOVERY_SCENARIOS),
        "budget_respected_rate": sum(
            bool(item["budget_respected"]) for item in strategy_runs
        ) / len(SCENARIOS),
        "success_score": success_score,
        "efficiency_score": efficiency_score,
        "recovery_score": recovery_score,
        "budget_score": budget_score,
        "total_score": success_score + efficiency_score + recovery_score + budget_score,
    }


def run_benchmark(
    output_dir: str | Path = ".loop/runs/benchmark-suite",
) -> dict[str, object]:
    """Run the complete scenario matrix and return evidence plus ranking."""

    root = Path(output_dir).resolve()
    runs = [
        _run_case(root, scenario, strategy)
        for scenario in SCENARIOS
        for strategy in STRATEGIES
    ]
    summaries = [_summarize(strategy, runs) for strategy in STRATEGIES]
    ranking = sorted(
        summaries,
        key=lambda item: (
            -float(item["total_score"]),
            float(item["average_success_steps"]),
            str(item["strategy"]),
        ),
    )
    return {
        "scenarios": list(SCENARIOS),
        "strategies": list(STRATEGIES),
        "runs": runs,
        "summaries": summaries,
        "ranking": ranking,
    }


def main() -> None:
    """Print the benchmark matrix and its strategy ranking as JSON."""

    print(json.dumps(run_benchmark(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
