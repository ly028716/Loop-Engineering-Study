"""Deterministic Diagnose -> Repair -> Verify learning experiment."""

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
from loop_engineering.diagnostics import DiagnosticFinding, diagnose_trace
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.policies import IncrementPolicy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached

from experiments.benchmark_suite import build_scenario
from experiments.failure_modes import build_experiment as build_failure_experiment

CASES = ("action_failure", "stalled_progress", "tight_budget")
TARGET_CODES = {
    "action_failure": ("action_failure",),
    "stalled_progress": ("stalled_progress", "budget_exhausted"),
    "tight_budget": ("budget_exhausted",),
}


def _build_baseline(case: str, root: Path) -> tuple[LoopRunner, LoopState, int]:
    if case == "action_failure":
        runner, state = build_failure_experiment("action_failure", root)
        return runner, state, 4
    if case == "stalled_progress":
        return build_scenario("stalled_progress", "fixed")
    if case == "tight_budget":
        return build_scenario("tight_budget", "fixed")
    raise ValueError(f"Unknown repair case: {case}")


def _build_repaired(case: str) -> tuple[LoopRunner, LoopState, int]:
    if case == "action_failure":
        return (
            LoopRunner(
                policy=IncrementPolicy(step_size=1.0),
                action=NumericAction(),
                evaluator=GoalEvaluator(tolerance=0.0),
                stop_conditions=[SuccessReached(), MaxSteps(4)],
            ),
            LoopState(step=0, value=0.0, goal=3.0),
            4,
        )
    if case in {"stalled_progress", "tight_budget"}:
        return build_scenario("steady_progress", "fixed")
    raise ValueError(f"Unknown repair case: {case}")


def _finding_payload(finding: DiagnosticFinding) -> dict[str, object]:
    payload = asdict(finding)
    payload["evidence_event_indices"] = list(finding.evidence_event_indices)
    return payload


def _summary(trace: LoopTrace, step_budget: int) -> dict[str, object]:
    findings = [_finding_payload(item) for item in diagnose_trace(trace, step_budget)]
    return {
        "success": trace.final_state is not None and trace.final_state.status == "SUCCEEDED",
        "diagnostic_codes": [item["code"] for item in findings],
        "findings": findings,
    }


def _save_report(path: Path, report: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run_case(root: Path, case: str) -> dict[str, object]:
    baseline_runner, baseline_state, baseline_budget = _build_baseline(case, root)
    repaired_runner, repaired_state, repaired_budget = _build_repaired(case)
    baseline_trace = baseline_runner.run(baseline_state)
    repaired_trace = repaired_runner.run(repaired_state)
    baseline_artifact = save_run_artifact(
        root / f"{case}.baseline.artifact.json",
        baseline_trace,
        MetricReport.from_trace(baseline_trace),
    )
    repaired_artifact = save_run_artifact(
        root / f"{case}.repaired.artifact.json",
        repaired_trace,
        MetricReport.from_trace(repaired_trace),
    )
    baseline = _summary(baseline_trace, baseline_budget)
    repaired = _summary(repaired_trace, repaired_budget)
    targets = set(TARGET_CODES[case])
    result = {
        "case": case,
        "target_diagnostic_codes": list(TARGET_CODES[case]),
        "baseline": baseline,
        "repaired": repaired,
        "baseline_artifact_path": str(baseline_artifact),
        "repaired_artifact_path": str(repaired_artifact),
        "repair_succeeded": bool(targets & set(baseline["diagnostic_codes"]))
        and bool(repaired["success"])
        and not (targets & set(repaired["diagnostic_codes"])),
    }
    report_path = _save_report(root / f"{case}.report.json", result)
    return {**result, "report_path": str(report_path)}


def run_repair_loop(
    output_dir: str | Path = ".loop/runs/diagnosis-repair-loop",
) -> list[dict[str, object]]:
    """Run each deterministic diagnosis-driven repair in declaration order."""

    root = Path(output_dir).resolve()
    return [_run_case(root, case) for case in CASES]


def main() -> None:
    """Print structured baseline and repaired-run evidence."""

    print(json.dumps(run_repair_loop(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
