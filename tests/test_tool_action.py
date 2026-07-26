import sys
from pathlib import Path

import pytest

from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.models import Feedback, LoopState
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached
from loop_engineering.tool_action import ToolAction
from loop_engineering.tool_adapters import (
    LocalToolAdapter,
    ToolAdapterError,
    ToolDefinition,
    ToolExecution,
)


def python_version_definition(tmp_path: Path) -> ToolDefinition:
    return ToolDefinition(
        name="python-version",
        executable=str(Path(sys.executable).resolve()),
        arguments=("--version",),
        working_directory=str(tmp_path.resolve()),
        timeout_seconds=2.0,
    )


class FixedDecisionPolicy(Policy):
    def __init__(self, decision: Decision) -> None:
        self.decision = decision

    def decide(
        self, state: LoopState, feedback: Feedback, recent_events=None
    ) -> Decision:
        del state, feedback, recent_events
        return self.decision


def test_tool_action_rejects_dynamic_decision_parameters(tmp_path: Path) -> None:
    action = ToolAction(LocalToolAdapter([python_version_definition(tmp_path)]))

    with pytest.raises(ToolAdapterError, match="parameters"):
        action.apply(
            LoopState(0, 0.0, 0.0),
            Decision("python-version", {"extra": 1.0}),
        )


def test_tool_action_maps_failed_execution_without_changing_numeric_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adapter = LocalToolAdapter([python_version_definition(tmp_path)])
    monkeypatch.setattr(
        adapter,
        "execute",
        lambda name: ToolExecution(
            success=False,
            exit_code=1,
            stdout="failure output",
            stderr="failure error",
            duration_seconds=0.25,
        ),
    )

    result = ToolAction(adapter).apply(
        LoopState(3, 4.0, 8.0), Decision("python-version", {})
    )

    assert result.success is False
    assert result.cost == 0.25
    assert result.state.step == 4
    assert result.state.value == 4.0


def test_tool_action_propagates_unknown_registered_name(tmp_path: Path) -> None:
    action = ToolAction(LocalToolAdapter([python_version_definition(tmp_path)]))

    with pytest.raises(ToolAdapterError, match="Unregistered tool"):
        action.apply(LoopState(0, 0.0, 0.0), Decision("unknown", {}))


def test_tool_action_keeps_trace_and_artifact_output_free(tmp_path: Path) -> None:
    trace = LoopRunner(
        FixedDecisionPolicy(Decision("python-version", {})),
        ToolAction(LocalToolAdapter([python_version_definition(tmp_path)])),
        GoalEvaluator(0.0),
        [SuccessReached(), MaxSteps(1)],
    ).run(LoopState(0, 0.0, 0.0))

    artifact = save_run_artifact(tmp_path / "artifact.json", trace)

    assert trace.final_state is not None
    assert trace.final_state.status == "SUCCEEDED"
    assert trace.events[2].payload.keys() == {"success", "cost"}
    assert "Python" not in artifact.read_text(encoding="utf-8")
