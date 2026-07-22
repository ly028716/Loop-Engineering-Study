"""Compare deterministic failure modes and their recovery outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import Evaluation, Evaluator, GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import Feedback, LoopState, LoopTrace
from loop_engineering.policies import Decision, IncrementPolicy, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


class FailOnceAction(Action):
    """Fail once and then apply normal numeric increments."""

    def __init__(self) -> None:
        self.failed = False
        self.numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if not self.failed:
            self.failed = True
            return ActionResult(
                state=state.with_value(state.value, injected_failure=True),
                success=False,
                cost=0.0,
            )
        return self.numeric_action.apply(state, decision)


class AlwaysFailAction(Action):
    """Never make progress, allowing the safety stop to be observed."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        del decision
        return ActionResult(
            state=state.with_value(state.value, persistent_failure=True),
            success=False,
            cost=0.0,
        )


class OscillatingAction(Action):
    """Alternate between increasing and decreasing the numeric value."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        del decision
        amount = 1.0 if state.step % 2 == 0 else -1.0
        return ActionResult(
            state=state.with_value(state.value + amount),
            success=True,
            cost=abs(amount),
        )


class RetryEvaluator(Evaluator):
    """Expose a retry signal when the action fails."""

    def __init__(self) -> None:
        self.goal_evaluator = GoalEvaluator(tolerance=0.0)

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        if not result.success:
            return Evaluation(
                score=0.0,
                success=False,
                message="Action failed; retry required",
                signals={"retry_required": 1.0},
            )
        return self.goal_evaluator.evaluate(before, result)


class SilentFailureEvaluator(RetryEvaluator):
    """Report failure without providing a recovery signal."""

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        if not result.success:
            return Evaluation(
                score=0.0,
                success=False,
                message="Action failed without recovery guidance",
                signals={},
            )
        return self.goal_evaluator.evaluate(before, result)


class FaultyEvaluator(Evaluator):
    """Reject every action to demonstrate evaluator disagreement."""

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        del before, result
        return Evaluation(
            score=0.0,
            success=False,
            message="Evaluator rejected the action",
            signals={"reported_error": 1.0},
        )


class RetryPolicy(Policy):
    """Increase the next action only when feedback requests a retry."""

    def decide(self, state: LoopState, feedback: Feedback) -> Decision:
        amount = 2.0 if feedback.signals.get("retry_required") else 1.0
        return Decision(
            name="increment",
            parameters={"amount": min(amount, max(state.goal - state.value, 0.0))},
        )


def build_experiment(
    failure_mode: str,
    output_dir: str | Path,
) -> tuple[LoopRunner, LoopState]:
    """Build an isolated runner for one failure-mode scenario."""

    del output_dir
    if failure_mode == "action_failure":
        policy: Policy = RetryPolicy()
        action: Action = FailOnceAction()
        evaluator: Evaluator = RetryEvaluator()
        conditions = [SuccessReached(), MaxSteps(4)]
        goal = 3.0
    elif failure_mode == "evaluator_disagreement":
        policy = IncrementPolicy(step_size=1.0)
        action = NumericAction()
        evaluator = FaultyEvaluator()
        conditions = [MaxSteps(1)]
        goal = 1.0
    elif failure_mode == "missing_feedback":
        policy = IncrementPolicy(step_size=1.0)
        action = FailOnceAction()
        evaluator = SilentFailureEvaluator()
        conditions = [SuccessReached(), MaxSteps(4)]
        goal = 3.0
    elif failure_mode == "oscillation":
        policy = IncrementPolicy(step_size=1.0)
        action = OscillatingAction()
        evaluator = GoalEvaluator(tolerance=0.0)
        conditions = [SuccessReached(), MaxSteps(6)]
        goal = 3.0
    elif failure_mode == "safety_limit":
        policy = IncrementPolicy(step_size=1.0)
        action = AlwaysFailAction()
        evaluator = GoalEvaluator(tolerance=0.0)
        conditions = [SuccessReached(), MaxSteps(3)]
        goal = 3.0
    else:
        raise ValueError(f"Unknown failure mode: {failure_mode}")

    return (
        LoopRunner(
            policy=policy,
            action=action,
            evaluator=evaluator,
            stop_conditions=conditions,
        ),
        LoopState(step=0, value=0.0, goal=goal),
    )


def _recovery_attempts(trace: LoopTrace) -> int:
    failed_indices = [
        index
        for index, event in enumerate(trace.events)
        if event.phase == "ACT" and event.payload.get("success") is False
    ]
    if not failed_indices:
        return 0
    first_failure = failed_indices[0]
    return sum(
        event.phase == "DECIDE" for event in trace.events[first_failure + 1 :]
    )


def _evidence_conflicts(trace: LoopTrace) -> int:
    if trace.final_state is None:
        return 0
    evaluations = [
        event for event in trace.events if event.phase == "EVALUATE"
    ]
    if not evaluations:
        return 0
    final_evaluation = evaluations[-1]
    reached_goal = trace.final_state.value == trace.final_state.goal
    rejected = final_evaluation.payload.get("success") is False
    return int(reached_goal and rejected)


def run_comparison(
    output_dir: str | Path = ".loop/runs/failure-modes",
) -> list[dict[str, object]]:
    """Run all failure modes and persist one Artifact per scenario."""

    root = Path(output_dir).resolve()
    results: list[dict[str, object]] = []
    modes = (
        "action_failure",
        "evaluator_disagreement",
        "missing_feedback",
        "oscillation",
        "safety_limit",
    )
    for failure_mode in modes:
        runner, initial_state = build_experiment(failure_mode, root)
        trace = runner.run(initial_state)
        report = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(
            root / f"{failure_mode}.json", trace, report
        )
        failure_count = sum(
            event.phase == "ACT" and event.payload.get("success") is False
            for event in trace.events
        )
        results.append(
            {
                "failure_mode": failure_mode,
                "status": trace.final_state.status if trace.final_state else "UNKNOWN",
                "success": report.success,
                "steps": report.steps,
                "final_score": report.final_score,
                "failure_count": failure_count,
                "recovery_attempts": _recovery_attempts(trace),
                "evidence_conflicts": _evidence_conflicts(trace),
                "stop_reason": str(trace.events[-1].payload["reason"]),
                "artifact_path": str(artifact_path),
            }
        )
    return results


def main() -> None:
    """Print failure-mode comparison results as JSON."""

    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
