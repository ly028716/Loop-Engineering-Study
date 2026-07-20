from loop_engineering.models import Feedback, LoopState
from loop_engineering.policies import IncrementPolicy


def test_increment_policy_uses_step_size_when_goal_is_far_away() -> None:
    state = LoopState(step=0, value=2.0, goal=10.0)

    decision = IncrementPolicy(step_size=3.0).decide(state, Feedback.empty())

    assert decision.name == "increment"
    assert decision.parameters == {"amount": 3.0}


def test_increment_policy_caps_amount_at_remaining_distance() -> None:
    state = LoopState(step=4, value=9.5, goal=10.0)

    decision = IncrementPolicy(step_size=3.0).decide(state, Feedback.empty())

    assert decision.parameters == {"amount": 0.5}


def test_increment_policy_returns_zero_after_goal_is_reached() -> None:
    state = LoopState(step=4, value=12.0, goal=10.0)

    decision = IncrementPolicy(step_size=3.0).decide(state, Feedback.empty())

    assert decision.parameters == {"amount": 0.0}
