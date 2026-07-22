from pathlib import Path

from experiments.feedback_strategies import (
    ErrorAwarePolicy,
    MemoryAwarePolicy,
    run_comparison,
)
from loop_engineering.models import Feedback, LoopEvent, LoopState


def test_error_aware_policy_uses_absolute_error_feedback() -> None:
    policy = ErrorAwarePolicy()
    state = LoopState(step=1, value=1.0, goal=6.0)

    decision = policy.decide(
        state,
        Feedback(score=0.2, message="not reached", signals={"absolute_error": 5.0}),
    )

    assert decision.parameters["amount"] == 2.0


def test_memory_aware_policy_reacts_to_failed_action_event() -> None:
    policy = MemoryAwarePolicy()
    state = LoopState(step=1, value=0.0, goal=6.0)
    history = [
        LoopEvent(step=1, phase="ACT", payload={"success": False, "cost": 0.0})
    ]

    decision = policy.decide(state, Feedback.empty(), history)

    assert decision.parameters["amount"] == 2.0


def test_run_comparison_returns_three_replayable_results(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)

    assert [item["strategy"] for item in results] == [
        "fixed",
        "error_aware",
        "memory_aware",
    ]
    assert all(item["success"] for item in results)
    assert all(Path(item["artifact_path"]).exists() for item in results)
