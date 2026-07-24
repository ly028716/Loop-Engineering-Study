"""Evaluate and select deterministic repair candidates using rerun evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.actions import NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.diagnostics import diagnose_trace
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState
from loop_engineering.policies import IncrementPolicy
from loop_engineering.repair_selection import (
    RepairCandidateEvaluation,
    rank_repair_candidates,
    select_best_repair,
)
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached

from experiments.diagnosis_repair_loop import (
    CASES,
    TARGET_CODES,
    _build_baseline,
    _summary,
)

CANDIDATES = {
    "action_failure": (
        ("replace_action_step_1", 1.0, 4),
        ("replace_action_step_1_5", 1.5, 4),
    ),
    "stalled_progress": (
        ("replace_action_step_1", 1.0, 8),
        ("replace_action_step_2", 2.0, 8),
    ),
    "tight_budget": (
        ("restore_budget_step_1", 1.0, 8),
        ("preserve_budget_step_2", 2.0, 3),
    ),
}


def _save_report(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _candidate_runner(case: str, step_size: float, step_budget: int) -> tuple[LoopRunner, LoopState]:
    if case not in CANDIDATES:
        raise ValueError(f"Unknown repair case: {case}")
    goal = 3.0 if case == "action_failure" else 6.0
    return (
        LoopRunner(
            policy=IncrementPolicy(step_size=step_size),
            action=NumericAction(),
            evaluator=GoalEvaluator(tolerance=0.0),
            stop_conditions=[SuccessReached(), MaxSteps(step_budget)],
        ),
        LoopState(step=0, value=0.0, goal=goal),
    )


def _candidate_payload(evaluation: RepairCandidateEvaluation) -> dict[str, object]:
    payload = asdict(evaluation)
    payload["diagnostic_codes"] = list(evaluation.diagnostic_codes)
    return payload


def _run_case(root: Path, case: str) -> dict[str, object]:
    declarations = CANDIDATES.get(case)
    if not declarations:
        raise ValueError(f"No repair candidates declared for case: {case}")
    baseline_runner, baseline_state, baseline_budget = _build_baseline(case, root)
    baseline_trace = baseline_runner.run(baseline_state)
    baseline_artifact = save_run_artifact(
        root / f"{case}.baseline.artifact.json",
        baseline_trace,
        MetricReport.from_trace(baseline_trace),
    )
    baseline = _summary(baseline_trace, baseline_budget)
    targets = set(TARGET_CODES[case])
    evaluations: list[RepairCandidateEvaluation] = []
    for index, (name, step_size, step_budget) in enumerate(declarations):
        runner, state = _candidate_runner(case, step_size, step_budget)
        trace = runner.run(state)
        metrics = MetricReport.from_trace(trace)
        artifact_path = save_run_artifact(root / f"{case}.{name}.artifact.json", trace, metrics)
        codes = tuple(item.code for item in diagnose_trace(trace, step_budget))
        evaluations.append(
            RepairCandidateEvaluation(
                name=name,
                declaration_index=index,
                succeeded=metrics.success,
                target_diagnostics_eliminated=not (targets & set(codes)),
                metrics=metrics,
                diagnostic_codes=codes,
                artifact_path=str(artifact_path),
            )
        )
    ranked = rank_repair_candidates(evaluations)
    selection = select_best_repair(ranked)
    return {
        "case": case,
        "target_diagnostic_codes": list(TARGET_CODES[case]),
        "baseline": baseline,
        "baseline_artifact_path": str(baseline_artifact),
        "candidates": [_candidate_payload(item) for item in ranked],
        "selected_candidate": selection.selected.name,
        "selected_artifact_path": selection.selected.artifact_path,
        "selection_reason": selection.reason,
        "repair_succeeded": selection.selected.succeeded
        and selection.selected.target_diagnostics_eliminated,
    }


def run_multi_repair_selection(
    output_dir: str | Path = ".loop/runs/multi-repair-selection",
) -> list[dict[str, object]]:
    """Rerun all declared candidates and select one for each repair case."""

    root = Path(output_dir).resolve()
    results = [_run_case(root, case) for case in CASES]
    _save_report(root / "report.json", results)
    return results


def main() -> None:
    print(json.dumps(run_multi_repair_selection(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
