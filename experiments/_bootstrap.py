"""Shared support for running experiment modules as direct scripts."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loop_engineering.models import LoopTrace


def prepare_script_imports(script_file: str) -> None:
    """Make the repository root importable when an experiment is run by path."""

    project_root = str(Path(script_file).resolve().parents[1])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def print_summary(trace: LoopTrace) -> None:
    """Print the stable command-line summary shared by every experiment."""

    from loop_engineering.metrics import MetricReport

    report = MetricReport.from_trace(trace)
    scores = [event.payload["score"] for event in trace.events if event.phase == "EVALUATE"]
    stop = trace.events[-1].payload
    print(f"steps={report.steps}")
    print(f"status={trace.final_state.status}")
    print(f"score={report.final_score}")
    print(f"stop_reason={stop['reason']}")
    print(f"scores={scores}")


def persist_and_print_summary(trace: LoopTrace, script_file: str) -> Path:
    """Save a direct experiment run and print its stable, replayable summary."""

    from loop_engineering.artifacts import save_run_artifact

    artifact_path = (
        Path(script_file).resolve().parents[1]
        / ".loop"
        / "runs"
        / f"{Path(script_file).stem}.json"
    )
    saved_path = save_run_artifact(artifact_path, trace)
    print_summary(trace)
    print(f"artifact_path={saved_path}")
    return saved_path
