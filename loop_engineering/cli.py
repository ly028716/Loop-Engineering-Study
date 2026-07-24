"""Command-line entry point for deterministic Loop Engineering runs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .actions import NumericAction
from .artifacts import load_run_artifact, save_run_artifact
from .evaluators import GoalEvaluator
from .metrics import MetricReport
from .models import LoopState, LoopTrace
from .policies import IncrementPolicy
from .runner import LoopRunner
from .stopping import MaxSteps, SuccessReached


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without performing a run."""

    parser = argparse.ArgumentParser(prog="loop-engineering")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run a deterministic numeric loop")
    run_parser.add_argument("--goal", type=float, required=True)
    run_parser.add_argument("--max-steps", type=int, default=20)
    run_parser.add_argument("--output", type=Path, required=True)
    replay_parser = subparsers.add_parser(
        "replay", help="print a complete saved artifact"
    )
    replay_parser.add_argument("artifact", type=Path)
    return parser


def run_loop(goal: float, max_steps: int) -> LoopTrace:
    """Run the built-in deterministic numeric loop from zero to ``goal``."""

    runner = LoopRunner(
        policy=IncrementPolicy(step_size=1.0),
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(max_steps)],
        safety_max_steps=max_steps,
    )
    return runner.run(LoopState(step=0, value=0.0, goal=goal))


def write_trace(
    path: Path,
    trace: LoopTrace,
    metrics: MetricReport | None = None,
) -> Path:
    """Persist a complete run artifact through the shared storage interface."""

    return save_run_artifact(path, trace, metrics)


def replay_artifact(path: Path) -> dict[str, object]:
    """Load one Artifact and return its complete JSON-ready run boundary."""

    trace, metrics = load_run_artifact(path)
    return {
        "artifact_path": str(path.resolve()),
        "events": [asdict(event) for event in trace.events],
        "final_state": asdict(trace.final_state) if trace.final_state else None,
        "metrics": asdict(metrics),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process-compatible exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "replay":
        json.dump(replay_artifact(args.artifact), fp=sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    if args.max_steps < 1:
        parser.error("--max-steps must be at least 1")

    trace = run_loop(args.goal, args.max_steps)
    report = MetricReport.from_trace(trace)
    trace_path = write_trace(args.output, trace, report)
    final_state = trace.final_state
    if final_state is None:
        raise RuntimeError("loop run completed without a final state")

    json.dump(
        {
            "status": final_state.status,
            "steps": report.steps,
            "final_value": final_state.value,
            "score": report.final_score,
            "trace_path": str(trace_path),
        },
        fp=sys.stdout,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
