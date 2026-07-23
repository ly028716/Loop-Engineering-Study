"""Run four deterministic Trace diagnostic cases and persist their evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.artifacts import save_run_artifact
from loop_engineering.diagnostics import DiagnosticFinding, diagnose_trace
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.runner import LoopRunner

from experiments.adaptive_strategy import build_experiment as build_adaptive_experiment
from experiments.benchmark_suite import build_scenario
from experiments.failure_modes import build_experiment as build_failure_experiment

CASES = ("action_failure", "stalled_progress", "tight_budget", "adaptive_recovery")


def _build_case(case: str, root: Path) -> tuple[LoopRunner, LoopState, int]:
    if case == "action_failure":
        runner, initial_state = build_failure_experiment("action_failure", root)
        return runner, initial_state, 4
    if case == "stalled_progress":
        return build_scenario("stalled_progress", "fixed")
    if case == "tight_budget":
        return build_scenario("tight_budget", "fixed")
    if case == "adaptive_recovery":
        runner, initial_state = build_adaptive_experiment("adaptive", root)
        return runner, initial_state, 8
    raise ValueError(f"Unknown diagnostic case: {case}")


def _finding_payload(finding: DiagnosticFinding) -> dict[str, object]:
    payload = asdict(finding)
    payload["evidence_event_indices"] = list(finding.evidence_event_indices)
    return payload


def _save_report(path: Path, report: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _run_case(root: Path, case: str) -> dict[str, object]:
    runner, initial_state, step_budget = _build_case(case, root)
    trace: LoopTrace = runner.run(initial_state)
    report = MetricReport.from_trace(trace)
    artifact_path = save_run_artifact(root / f"{case}.artifact.json", trace, report)
    findings = [
        _finding_payload(finding)
        for finding in diagnose_trace(trace, step_budget)
    ]
    result = {
        "case": case,
        "artifact_path": str(artifact_path),
        "step_budget": step_budget,
        "findings": findings,
    }
    report_path = _save_report(root / f"{case}.report.json", result)
    return {**result, "report_path": str(report_path)}


def run_diagnostics(
    output_dir: str | Path = ".loop/runs/trace-diagnostics",
) -> list[dict[str, object]]:
    """Run the deterministic diagnostic matrix in its documented order."""

    root = Path(output_dir).resolve()
    return [_run_case(root, case) for case in CASES]


def main() -> None:
    """Print all persisted diagnostic records as JSON."""

    print(json.dumps(run_diagnostics(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
