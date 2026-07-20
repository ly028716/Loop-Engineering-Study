import pytest

from loop_engineering.evaluators import Evaluation
from loop_engineering.models import LoopState
from loop_engineering.stopping import MaxSteps, SuccessReached


def evaluation(*, success: bool) -> Evaluation:
    return Evaluation(
        score=1.0 if success else 0.5,
        success=success,
        message="Goal reached" if success else "Goal not reached",
        signals={},
    )


def test_success_reached_stops_with_succeeded_status() -> None:
    decision = SuccessReached().should_stop(
        LoopState(step=1, value=1.0, goal=1.0), evaluation(success=True), []
    )

    assert decision.stop is True
    assert decision.status == "SUCCEEDED"
    assert decision.reason == "Evaluation reported success"


def test_success_reached_continues_when_evaluation_is_not_successful() -> None:
    decision = SuccessReached().should_stop(
        LoopState(step=1, value=0.0, goal=1.0), evaluation(success=False), []
    )

    assert decision.stop is False
    assert decision.status == "RUNNING"
    assert decision.reason == ""


def test_max_steps_stops_at_the_configured_step_limit() -> None:
    decision = MaxSteps(2).should_stop(
        LoopState(step=2, value=1.0, goal=3.0), evaluation(success=False), []
    )

    assert decision.stop is True
    assert decision.status == "STOPPED"
    assert decision.reason == "Reached maximum steps: 2"


def test_max_steps_rejects_non_positive_limits() -> None:
    with pytest.raises(ValueError, match="max_steps must be at least 1"):
        MaxSteps(0)
