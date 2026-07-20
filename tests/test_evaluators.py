from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.models import LoopState
from loop_engineering.actions import ActionResult


def test_goal_evaluator_scores_by_absolute_error() -> None:
    before = LoopState(step=0, value=0.0, goal=10.0)
    result = ActionResult(
        state=LoopState(step=1, value=8.0, goal=10.0), success=True, cost=8.0
    )

    evaluation = GoalEvaluator(tolerance=0.5).evaluate(before, result)

    assert evaluation.score == 1 / 3
    assert evaluation.success is False
    assert evaluation.signals == {"absolute_error": 2.0}


def test_goal_evaluator_accepts_error_at_tolerance_boundary() -> None:
    before = LoopState(step=0, value=0.0, goal=10.0)
    result = ActionResult(
        state=LoopState(step=1, value=10.5, goal=10.0), success=True, cost=10.5
    )

    evaluation = GoalEvaluator(tolerance=0.5).evaluate(before, result)

    assert evaluation.score == 1 / 1.5
    assert evaluation.success is True
    assert evaluation.message == "Goal reached"
