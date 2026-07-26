"""Diagnostic-only teaching example for the controlled local tool adapter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.policies import Decision, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached
from loop_engineering.tool_action import ToolAction
from loop_engineering.tool_adapters import LocalToolAdapter, ToolDefinition


class PythonVersionPolicy(Policy):
    """Select the one explicitly registered diagnostic command."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: list[LoopEvent] | None = None,
    ) -> Decision:
        del state, feedback, recent_events
        return Decision("python-version", {})


def run_local_tool_adapter_demo(
    output_dir: str | Path = ".loop/runs/local-tool-adapter",
) -> dict[str, object]:
    """Run one safe Python-version diagnostic command through the loop."""

    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    definition = ToolDefinition(
        name="python-version",
        executable=str(Path(sys.executable).resolve()),
        arguments=("--version",),
        working_directory=str(root),
        timeout_seconds=2.0,
    )
    action = ToolAction(LocalToolAdapter([definition]))
    trace = LoopRunner(
        policy=PythonVersionPolicy(),
        action=action,
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(1)],
    ).run(LoopState(step=0, value=0.0, goal=0.0))
    execution = action.last_execution
    if execution is None:
        raise RuntimeError("The Python-version tool did not execute")

    artifact_path = save_run_artifact(root / "artifact.json", trace)
    report = {
        "artifact_path": str(artifact_path),
        "status": trace.final_state.status if trace.final_state else "RUNNING",
        "tool_name": definition.name,
        "exit_code": execution.exit_code,
        "duration_seconds": execution.duration_seconds,
        "output": execution.stdout + execution.stderr,
    }
    (root / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    """Print the replayable diagnostic-only teaching report."""

    print(json.dumps(run_local_tool_adapter_demo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
