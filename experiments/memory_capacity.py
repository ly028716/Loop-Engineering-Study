"""Compare loop recovery with different event-memory capacities."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.memory import WorkingMemory
from loop_engineering.metrics import MetricReport
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


MEMORY_CAPACITIES = {
    "no_memory": 1,
    "short_memory": 7,
    "working_memory": 21,
    "long_window": 1_000,
}


class FailureScheduleAction(Action):
    """Fail on configured one-based calls and succeed on every other call."""

    def __init__(self, failure_calls: set[int]) -> None:
        self.failure_calls = set(failure_calls)
        self.call_count = 0
        self._numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        self.call_count += 1
        if self.call_count in self.failure_calls:
            return ActionResult(
                state=state.with_value(state.value, scheduled_failure=True),
                success=False,
                cost=0.0,
            )
        return self._numeric_action.apply(state, decision)


class MemoryRecoveryPolicy(Policy):
    """Increase the next action when a failed action remains in memory."""

    def __init__(self, ignore_history: bool = False) -> None:
        self.ignore_history = ignore_history

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        history = [] if self.ignore_history else list(recent_events or [])
        remembers_failure = any(
            event.phase == "ACT" and event.payload.get("success") is False
            for event in history
        )
        amount = 2.0 if remembers_failure else 1.0
        return Decision(
            name="increment",
            parameters={"amount": min(amount, max(state.goal - state.value, 0.0))},
        )


def build_experiment(
    memory_mode: str,
    output_dir: str | Path,
) -> tuple[LoopRunner, LoopState, int]:
    """Build an isolated runner for one memory-capacity configuration."""

    del output_dir
    try:
        capacity = MEMORY_CAPACITIES[memory_mode]
    except KeyError as error:
        raise ValueError(f"Unknown memory mode: {memory_mode}") from error

    policy = MemoryRecoveryPolicy(ignore_history=memory_mode == "no_memory")
    runner = LoopRunner(
        policy=policy,
        action=FailureScheduleAction(failure_calls={1, 4}),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(12)],
        memory=WorkingMemory(capacity=capacity),
    )
    return runner, LoopState(step=0, value=0.0, goal=6.0), capacity


def run_comparison(output_dir: str | Path = ".loop/runs/memory-capacity") -> list[dict[str, object]]:
    """Run all memory modes and persist one complete artifact per mode."""

    root = Path(output_dir).resolve()
    results: list[dict[str, object]] = []
    for memory_mode in MEMORY_CAPACITIES:
        runner, initial_state, capacity = build_experiment(memory_mode, root)
        trace = runner.run(initial_state)
        report = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(root / f"{memory_mode}.json", trace, report)
        failure_count = sum(
            event.phase == "ACT" and event.payload.get("success") is False
            for event in trace.events
        )
        recovery_action_count = sum(
            event.phase == "DECIDE" and event.payload.get("parameters", {}).get("amount") == 2.0
            for event in trace.events
        )
        results.append(
            {
                "memory_mode": memory_mode,
                "capacity": capacity,
                **asdict(report),
                "failure_count": failure_count,
                "recovery_action_count": recovery_action_count,
                "stop_reason": str(trace.events[-1].payload["reason"]),
                "artifact_path": str(artifact_path),
            }
        )
    return results


def main() -> None:
    """Print memory-capacity comparison results as JSON."""

    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
