"""A loop where an action reaches the target but a faulty evaluator rejects it."""

from __future__ import annotations

if __package__:
    from ._bootstrap import persist_and_print_summary
else:
    from _bootstrap import prepare_script_imports, persist_and_print_summary
    prepare_script_imports(__file__)

from loop_engineering.actions import ActionResult, NumericAction
from loop_engineering.evaluators import Evaluation, Evaluator
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.policies import IncrementPolicy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps


class FaultyEvaluator(Evaluator):
    """Incorrectly rejects a successful state to separate action from evaluation."""

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        return Evaluation(
            score=0.0,
            success=False,
            message="Faulty evaluator rejected the applied action",
            signals={"reported_error": 1.0},
        )


def run() -> LoopTrace:
    """Reach the numeric goal while the faulty evaluator prevents success stopping."""

    runner = LoopRunner(
        policy=IncrementPolicy(step_size=1.0),
        action=NumericAction(),
        evaluator=FaultyEvaluator(),
        stop_conditions=[MaxSteps(1)],
    )
    return runner.run(LoopState(step=0, value=0.0, goal=1.0))


def main() -> None:
    """Print the completed trace summary for command-line exploration."""

    persist_and_print_summary(run(), __file__)


if __name__ == "__main__":
    main()
