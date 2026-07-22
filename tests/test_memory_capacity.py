from pathlib import Path

from experiments.memory_capacity import (
    FailureScheduleAction,
    MemoryRecoveryPolicy,
    run_comparison,
)
from loop_engineering.artifacts import load_run_artifact
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.policies import Decision


def test_failure_schedule_fails_only_on_calls_one_and_four() -> None:
    action = FailureScheduleAction(failure_calls={1, 4})
    state = LoopState(step=0, value=0.0, goal=6.0)
    decision = Decision(name="increment", parameters={"amount": 1.0})

    results = [action.apply(state, decision) for _ in range(4)]

    assert [result.success for result in results] == [False, True, True, False]


def test_memory_recovery_policy_reacts_to_failed_action() -> None:
    policy = MemoryRecoveryPolicy()
    state = LoopState(step=1, value=0.0, goal=6.0)
    history = [
        LoopEvent(step=1, phase="ACT", payload={"success": False, "cost": 0.0})
    ]

    decision = policy.decide(state, Feedback.empty(), history)

    assert decision.parameters["amount"] == 2.0


def test_run_comparison_returns_all_memory_modes(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)

    assert [item["memory_mode"] for item in results] == [
        "no_memory",
        "short_memory",
        "working_memory",
        "long_window",
    ]
    assert all(item["success"] for item in results)
    assert all(Path(item["artifact_path"]).exists() for item in results)
    assert all(item["failure_count"] == 2 for item in results)
    for item in results:
        trace, report = load_run_artifact(item["artifact_path"])
        assert trace.events
        assert report.success is True
