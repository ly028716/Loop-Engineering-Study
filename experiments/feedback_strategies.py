"""Compare fixed, feedback-aware, and memory-aware loop policies."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import Feedback, LoopEvent, LoopState, LoopTrace
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


def _amount_for_remaining(state: LoopState, amount: float) -> float:
    """Keep a decision bounded by the remaining distance to the goal."""

    return min(amount, max(state.goal - state.value, 0.0))


class FixedIncrementPolicy(Policy):
    """Ignore feedback and use a constant bounded increment."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        return Decision(
            name="increment",
            parameters={"amount": _amount_for_remaining(state, 1.0)},
        )


class ErrorAwarePolicy(Policy):
    """Use evaluator error feedback to take larger steps when far from the goal."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        error = float(feedback.signals.get("absolute_error", 0.0))
        amount = 2.0 if error > 1.0 else 1.0
        return Decision(
            name="increment",
            parameters={"amount": _amount_for_remaining(state, amount)},
        )


class MemoryAwarePolicy(Policy):
    """Use recent failures or stalled scores to choose a larger increment."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        events = list(recent_events or [])
        failed_action = any(
            event.phase == "ACT" and event.payload.get("success") is False
            for event in events
        )
        evaluations = [
            event
            for event in events
            if event.phase == "EVALUATE" and "score" in event.payload
        ]
        stalled = len(evaluations) >= 2 and all(
            float(event.payload["score"]) == float(evaluations[-1].payload["score"])
            for event in evaluations[-2:]
        )
        amount = 2.0 if failed_action or stalled else 1.0
        return Decision(
            name="increment",
            parameters={"amount": _amount_for_remaining(state, amount)},
        )


class FailOnceAction(Action):
    """Fail once without progress so memory can observe and react to it."""

    def __init__(self) -> None:
        self._has_failed = False
        self._numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if not self._has_failed:
            self._has_failed = True
            return ActionResult(
                state=state.with_value(state.value, injected_failure=True),
                success=False,
                cost=0.0,
            )
        return self._numeric_action.apply(state, decision)


def build_experiment(
    strategy: str,
    output_dir: str | Path,
) -> tuple[LoopRunner, LoopState]:
    """Build one isolated runner for a named comparison strategy."""

    del output_dir
    policies: dict[str, type[Policy]] = {
        "fixed": FixedIncrementPolicy,
        "error_aware": ErrorAwarePolicy,
        "memory_aware": MemoryAwarePolicy,
    }
    try:
        policy = policies[strategy]()
    except KeyError as error:
        raise ValueError(f"Unknown feedback strategy: {strategy}") from error

    action: Action = FailOnceAction() if strategy == "memory_aware" else NumericAction()
    runner = LoopRunner(
        policy=policy,
        action=action,
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(10)],
    )
    return runner, LoopState(step=0, value=0.0, goal=6.0)


def run_comparison(output_dir: str | Path = ".loop/runs/feedback-strategies") -> list[dict[str, object]]:
    """Run all strategies and persist one complete artifact per strategy."""

    root = Path(output_dir).resolve()
    results: list[dict[str, object]] = []
    for strategy in ("fixed", "error_aware", "memory_aware"):
        runner, initial_state = build_experiment(strategy, root)
        trace = runner.run(initial_state)
        report = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(root / f"{strategy}.json", trace, report)
        stop_reason = str(trace.events[-1].payload["reason"])
        results.append(
            {
                "strategy": strategy,
                **asdict(report),
                "stop_reason": stop_reason,
                "artifact_path": str(artifact_path),
            }
        )
    return results


def main() -> None:
    """Print comparison results as one JSON document."""

    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
