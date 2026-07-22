import pytest

from loop_engineering.evaluators import Evaluation
from loop_engineering.models import LoopEvent, LoopState
from loop_engineering.stopping import MaxSteps, NoProgress, SuccessReached


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


def test_no_progress_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError, match="window must be at least 1"):
        NoProgress(window=0)
    with pytest.raises(ValueError, match="min_score_gain cannot be negative"):
        NoProgress(window=2, min_score_gain=-0.1)


def test_no_progress_waits_for_window_and_stops_on_flat_scores() -> None:
    condition = NoProgress(window=3)
    history = [
        LoopEvent(step=1, phase="EVALUATE", payload={"score": 0.5}),
        LoopEvent(step=2, phase="EVALUATE", payload={"score": 0.5}),
        LoopEvent(step=3, phase="EVALUATE", payload={"score": 0.5}),
    ]

    decision = condition.should_stop(
        LoopState(step=3, value=0.0, goal=1.0), evaluation(success=False), history
    )

    assert decision.stop is True
    assert decision.reason == "No progress for 3 evaluations"


def test_no_progress_continues_when_score_improves() -> None:
    condition = NoProgress(window=3)
    history = [
        LoopEvent(step=1, phase="EVALUATE", payload={"score": 0.2}),
        LoopEvent(step=2, phase="EVALUATE", payload={"score": 0.4}),
        LoopEvent(step=3, phase="EVALUATE", payload={"score": 0.5}),
    ]

    decision = condition.should_stop(
        LoopState(step=3, value=2.0, goal=3.0), evaluation(success=False), history
    )

    assert decision.stop is False
