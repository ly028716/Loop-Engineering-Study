"""Compare deterministic diagnosis-repair Trace pairs without replaying them."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from loop_engineering.artifacts import load_run_artifact
from loop_engineering.trace_diff import compare_traces

from experiments.diagnosis_repair_loop import run_repair_loop


def _save_report(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _comparison_payload(comparison: object) -> dict[str, object]:
    payload = asdict(comparison)
    first_difference = payload["first_difference"]
    if first_difference is not None:
        first_difference["field_path"] = list(first_difference["field_path"])
    return payload


def run_trace_diff_analysis(
    output_dir: str | Path = ".loop/runs/trace-diff-analysis",
) -> list[dict[str, object]]:
    """Generate and compare every deterministic diagnosis-repair Artifact pair."""

    root = Path(output_dir).resolve()
    repair_results = run_repair_loop(root / "repair-loop")
    results: list[dict[str, object]] = []
    for repair_result in repair_results:
        baseline_trace, baseline_metrics = load_run_artifact(
            repair_result["baseline_artifact_path"]
        )
        repaired_trace, repaired_metrics = load_run_artifact(
            repair_result["repaired_artifact_path"]
        )
        comparison = compare_traces(
            baseline_trace, repaired_trace, baseline_metrics, repaired_metrics
        )
        results.append(
            {
                "case": repair_result["case"],
                "baseline_artifact_path": repair_result["baseline_artifact_path"],
                "repaired_artifact_path": repair_result["repaired_artifact_path"],
                "repair_succeeded": repair_result["repair_succeeded"],
                "comparison": _comparison_payload(comparison),
            }
        )
    _save_report(root / "report.json", results)
    return results


def main() -> None:
    """Print the persisted Trace difference report as JSON."""

    print(json.dumps(run_trace_diff_analysis(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
