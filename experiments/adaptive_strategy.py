"""Deterministic comparison of adaptive loop-decision strategies."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import Evaluation, Evaluator, GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import Feedback, LoopEvent, LoopState, LoopTrace
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


def _remaining_amount(state: LoopState, amount: float) -> float:
    """Limit an increment to the positive distance remaining to the goal."""

    return min(amount, max(state.goal - state.value, 0.0))


class FailOnSecondAction(Action):
    """Inject one no-cost failure when the second action is attempted."""

    def __init__(self) -> None:
        self._numeric_action = NumericAction()
        self._failed = False

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if state.step == 1 and not self._failed:
            self._failed = True
            return ActionResult(
                state=state.with_value(state.value, injected_failure=True),
                success=False,
                cost=0.0,
            )
        return self._numeric_action.apply(state, decision)


class FixedPolicy(Policy):
    """Advance in bounded unit increments."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del feedback, recent_events
        return Decision("increment", {"amount": _remaining_amount(state, 1.0)})


class ErrorAwarePolicy(Policy):
    """Take larger increments while the evaluated error remains large."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del recent_events
        amount = 4.0 if feedback.signals.get("absolute_error", state.goal) > 2.0 else 1.0
        return Decision("increment", {"amount": _remaining_amount(state, amount)})


class MemoryAwarePolicy(Policy):
    """Use a larger increment after an observed failed action."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del feedback
        failed_action = any(
            event.phase == "ACT" and event.payload.get("success") is False
            for event in recent_events or ()
        )
        amount = 4.0 if failed_action else 1.0
        return Decision("increment", {"amount": _remaining_amount(state, amount)})


class AdaptivePolicy(Policy):
    """Choose a numeric mode from the current failure, progress, and budget."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del recent_events
        remaining = state.goal - state.value
        failed = feedback.signals.get("action_success") is False
        if failed:
            mode_code, amount = 3.0, 1.0
        elif remaining <= 2.0:
            mode_code, amount = 2.0, 1.0
        elif state.step >= 6:
            mode_code, amount = 4.0, 1.0
        else:
            mode_code, amount = 1.0, 4.0
        return Decision(
            "increment",
            {"amount": _remaining_amount(state, amount), "mode_code": mode_code},
        )


class RecoveryAwareEvaluator(Evaluator):
    """Preserve goal evaluation while exposing action success as feedback."""

    def __init__(self) -> None:
        self._goal_evaluator = GoalEvaluator(tolerance=0.0)

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        evaluation = self._goal_evaluator.evaluate(before, result)
        return Evaluation(
            score=evaluation.score,
            success=evaluation.success,
            message=evaluation.message,
            signals={**evaluation.signals, "action_success": result.success},
        )


def build_experiment(strategy: str, output_dir: str | Path) -> tuple[LoopRunner, LoopState]:
    """Build an isolated runner and its shared deterministic initial state."""

    del output_dir
    policies: dict[str, Policy] = {
        "fixed": FixedPolicy(),
        "error_aware": ErrorAwarePolicy(),
        "memory_aware": MemoryAwarePolicy(),
        "adaptive": AdaptivePolicy(),
    }
    if strategy not in policies:
        raise ValueError(f"Unknown adaptive strategy: {strategy}")
    return (
        LoopRunner(
            policy=policies[strategy],
            action=FailOnSecondAction(),
            evaluator=RecoveryAwareEvaluator(),
            stop_conditions=[SuccessReached(), MaxSteps(8)],
        ),
        LoopState(step=0, value=0.0, goal=6.0),
    )


def _adaptive_counts(trace: LoopTrace) -> tuple[int, int]:
    mode_codes = [
        event.payload["parameters"].get("mode_code")
        for event in trace.events
        if event.phase == "DECIDE" and "mode_code" in event.payload["parameters"]
    ]
    switch_count = sum(
        previous != current for previous, current in zip(mode_codes, mode_codes[1:])
    )
    recovery_count = sum(mode_code == 3.0 for mode_code in mode_codes)
    return switch_count, recovery_count


def run_comparison(
    output_dir: str | Path = ".loop/runs/adaptive-strategy",
) -> list[dict[str, object]]:
    """Run, persist, and summarize each strategy in deterministic order."""

    destination = Path(output_dir)
    results: list[dict[str, object]] = []
    for strategy in ("fixed", "error_aware", "memory_aware", "adaptive"):
        runner, initial_state = build_experiment(strategy, destination)
        trace = runner.run(initial_state)
        report = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(destination / f"{strategy}.json", trace, report)
        switch_count, recovery_count = _adaptive_counts(trace) if strategy == "adaptive" else (0, 0)
        stop_event = trace.events[-1]
        results.append(
            {
                "strategy": strategy,
                "status": trace.final_state.status if trace.final_state else "RUNNING",
                "success": report.success,
                "steps": report.steps,
                "final_score": report.final_score,
                "switch_count": switch_count,
                "recovery_count": recovery_count,
                "stop_reason": stop_event.payload["reason"],
                "artifact_path": str(artifact_path),
            }
        )
    return results


def main() -> None:
    """Print the deterministic strategy comparison."""

    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
