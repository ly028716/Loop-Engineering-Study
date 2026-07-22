"""Compare convergence, stalled, and oscillating loop termination."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.actions import Action, ActionResult, NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState
from loop_engineering.policies import Decision, IncrementPolicy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, NoProgress, SuccessReached


class StalledAction(Action):
    """Advance the loop counter without changing the value."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        del decision
        return ActionResult(
            state=state.with_value(state.value),
            success=True,
            cost=0.0,
        )


class OscillatingAction(Action):
    """Move one step forward and one step backward on alternating rounds."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        del decision
        amount = 1.0 if state.step % 2 == 0 else -1.0
        return ActionResult(
            state=state.with_value(state.value + amount),
            success=True,
            cost=abs(amount),
        )


def build_experiment(
    mode: str,
    output_dir: str | Path,
) -> tuple[LoopRunner, LoopState]:
    """Build an isolated runner for one convergence mode."""

    del output_dir
    conditions = [SuccessReached(), NoProgress(window=3), MaxSteps(max_steps=6)]
    if mode == "converging":
        action: Action = NumericAction()
        policy = IncrementPolicy(step_size=1.0)
    elif mode == "stalled":
        action = StalledAction()
        policy = IncrementPolicy(step_size=1.0)
    elif mode == "oscillating":
        action = OscillatingAction()
        policy = IncrementPolicy(step_size=1.0)
    else:
        raise ValueError(f"Unknown convergence mode: {mode}")

    return (
        LoopRunner(
            policy=policy,
            action=action,
            evaluator=GoalEvaluator(tolerance=0.0),
            stop_conditions=conditions,
        ),
        LoopState(step=0, value=0.0, goal=3.0),
    )


def run_comparison(
    output_dir: str | Path = ".loop/runs/convergence-stopping",
) -> list[dict[str, object]]:
    """Run all convergence modes and persist one Artifact per mode."""

    root = Path(output_dir).resolve()
    results: list[dict[str, object]] = []
    for mode in ("converging", "stalled", "oscillating"):
        runner, initial_state = build_experiment(mode, root)
        trace = runner.run(initial_state)
        report = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(root / f"{mode}.json", trace, report)
        score_history = [
            float(event.payload["score"])
            for event in trace.events
            if event.phase == "EVALUATE" and "score" in event.payload
        ]
        results.append(
            {
                "mode": mode,
                **asdict(report),
                "score_history": score_history,
                "stop_reason": str(trace.events[-1].payload["reason"]),
                "artifact_path": str(artifact_path),
            }
        )
    return results


def main() -> None:
    """Print convergence comparison results as JSON."""

    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
