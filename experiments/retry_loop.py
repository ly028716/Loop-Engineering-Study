"""A deterministic failed action whose feedback changes the next decision."""

from __future__ import annotations

if __package__:
    from ._bootstrap import persist_and_print_summary
else:
    from _bootstrap import prepare_script_imports, persist_and_print_summary
    prepare_script_imports(__file__)

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.evaluators import Evaluation, Evaluator, GoalEvaluator
from loop_engineering.models import Feedback, LoopState, LoopTrace
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


class FailOnceAction(Action):
    """Fail the first action without changing the value, then increment normally."""

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


class RetryAwareEvaluator(Evaluator):
    """Convert the injected failure into feedback a policy can act upon."""

    def __init__(self) -> None:
        self._goal_evaluator = GoalEvaluator(tolerance=0.0)

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        if not result.success:
            return Evaluation(
                score=0.0,
                success=False,
                message="Injected action failure; retry with a larger increment",
                signals={"retry_required": 1.0},
            )
        return self._goal_evaluator.evaluate(before, result)


class FeedbackRetryPolicy(Policy):
    """Use retry feedback to select a larger second action."""

    def decide(self, state: LoopState, feedback: Feedback) -> Decision:
        amount = 2.0 if feedback.signals.get("retry_required") else 1.0
        return Decision(
            name="increment",
            parameters={"amount": min(amount, max(state.goal - state.value, 0.0))},
        )


def run() -> LoopTrace:
    """Run one injected failure followed by feedback-driven recovery."""

    runner = LoopRunner(
        policy=FeedbackRetryPolicy(),
        action=FailOnceAction(),
        evaluator=RetryAwareEvaluator(),
        stop_conditions=[SuccessReached(), MaxSteps(4)],
    )
    return runner.run(LoopState(step=0, value=0.0, goal=3.0))


def main() -> None:
    """Print the completed trace summary for command-line exploration."""

    persist_and_print_summary(run(), __file__)


if __name__ == "__main__":
    main()
