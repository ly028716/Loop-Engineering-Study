import pytest

from loop_engineering.actions import NumericAction
from loop_engineering.policies import Decision
from loop_engineering.models import LoopState


def test_numeric_action_applies_increment_to_a_new_state() -> None:
    before = LoopState(step=2, value=4.0, goal=10.0)

    result = NumericAction().apply(before, Decision("increment", {"amount": 2.5}))

    assert result.success is True
    assert result.cost == 2.5
    assert result.state.step == 3
    assert result.state.value == 6.5
    assert before.value == 4.0


def test_numeric_action_rejects_unknown_decisions() -> None:
    state = LoopState(step=0, value=0.0, goal=1.0)

    with pytest.raises(ValueError, match="Unsupported decision"):
        NumericAction().apply(state, Decision("decrement", {"amount": 1.0}))
