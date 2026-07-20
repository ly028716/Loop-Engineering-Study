"""A stable numeric loop that approaches and reaches its target."""

from __future__ import annotations

if __package__:
    from ._bootstrap import persist_and_print_summary
else:
    from _bootstrap import prepare_script_imports, persist_and_print_summary
    prepare_script_imports(__file__)

from loop_engineering.actions import NumericAction
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.models import LoopTrace, LoopState
from loop_engineering.policies import IncrementPolicy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


def run() -> LoopTrace:
    """Run a bounded, deterministic approach from zero to five."""

    runner = LoopRunner(
        policy=IncrementPolicy(step_size=2.0),
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(5)],
    )
    return runner.run(LoopState(step=0, value=0.0, goal=5.0))


def main() -> None:
    """Print the completed trace summary for command-line exploration."""

    persist_and_print_summary(run(), __file__)


if __name__ == "__main__":
    main()
