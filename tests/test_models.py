from dataclasses import FrozenInstanceError

import pytest


def test_loop_state_with_value_returns_an_incremented_copy() -> None:
    from loop_engineering.models import LoopState

    state = LoopState(
        step=0,
        value=0.0,
        goal=3.0,
        metadata={"source": "initial"},
    )

    updated = state.with_value(1.0, source="action", accepted=True)

    assert state.step == 0
    assert state.value == 0.0
    assert state.metadata == {"source": "initial"}
    assert updated.step == 1
    assert updated.value == 1.0
    assert updated.goal == 3.0
    assert updated.status == "RUNNING"
    assert updated.metadata == {"source": "action", "accepted": True}

    with pytest.raises(FrozenInstanceError):
        state.value = 2.0


def test_feedback_empty_returns_neutral_feedback() -> None:
    from loop_engineering.models import Feedback

    assert Feedback.empty() == Feedback(score=0.0, message="", signals={})


def test_loop_event_rejects_an_unknown_phase() -> None:
    from loop_engineering.models import LoopEvent

    with pytest.raises(ValueError, match="Unsupported loop phase"):
        LoopEvent(step=0, phase="INVALID", payload={})


def test_loop_trace_append_creates_a_valid_event() -> None:
    from loop_engineering.models import LoopTrace

    trace = LoopTrace()
    trace.append("OBSERVE", step=2, payload={"value": 1.0})

    assert trace.events[0].step == 2
    assert trace.events[0].phase == "OBSERVE"
    assert trace.events[0].payload == {"value": 1.0}
    assert trace.final_state is None
