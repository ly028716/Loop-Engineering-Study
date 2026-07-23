"""Semantic regression gate for the executable learning experiments."""

from __future__ import annotations

import json
from pathlib import Path

if __package__:
    from ._bootstrap import prepare_script_imports
else:
    from _bootstrap import prepare_script_imports

    prepare_script_imports(__file__)

from experiments.benchmark_suite import run_benchmark
from experiments.diagnosis_repair_loop import run_repair_loop
from experiments.sensitivity_analysis import BASELINE, run_sensitivity
from experiments.trace_diagnostics import run_diagnostics


def _check(name: str, passed: bool, evidence: str) -> dict[str, object]:
    return {"name": name, "passed": passed, "evidence": evidence}


def _benchmark_check(root: Path) -> dict[str, object]:
    result = run_benchmark(root / "benchmark")
    scores = {item["strategy"]: float(item["total_score"]) for item in result["summaries"]}
    passed = len(result["runs"]) == 20 and len(result["summaries"]) == 4 and scores["adaptive"] > scores["fixed"]
    return _check("benchmark", passed, f"runs={len(result['runs'])}; adaptive={scores['adaptive']}; fixed={scores['fixed']}")


def _sensitivity_check(root: Path) -> dict[str, object]:
    result = run_sensitivity(root / "sensitivity")
    isolated = all(
        all(values[key] == BASELINE[key] for key in BASELINE if key != config["parameter_family"])
        for config in result["configurations"]
        for values in [config["parameters"]]
    )
    passed = len(result["configurations"]) == 9 and len(result["runs"]) == 36 and isolated and result["flip_analysis"]["goal_distance"]["no_flip"] is True
    return _check("sensitivity", passed, f"configurations={len(result['configurations'])}; runs={len(result['runs'])}; goal_distance_no_flip={result['flip_analysis']['goal_distance']['no_flip']}")


def _diagnostics_check(root: Path) -> dict[str, object]:
    result = run_diagnostics(root / "diagnostics")
    codes = {finding["code"] for item in result for finding in item["findings"]}
    paths_exist = all(Path(item[key]).exists() for item in result for key in ("artifact_path", "report_path"))
    expected = {"action_failure", "stalled_progress", "budget_exhausted", "recovery_observed"}
    return _check("diagnostics", len(result) == 4 and codes == expected and paths_exist, f"cases={len(result)}; codes={sorted(codes)}; outputs_exist={paths_exist}")


def _repair_check(root: Path) -> dict[str, object]:
    result = run_repair_loop(root / "repair-loop")
    passed = len(result) == 3 and all(
        item["repair_succeeded"] and item["repaired"]["success"] and not (set(item["target_diagnostic_codes"]) & set(item["repaired"]["diagnostic_codes"]))
        for item in result
    )
    return _check("repair_loop", passed, f"cases={len(result)}; repaired={[item['repair_succeeded'] for item in result]}")


def run_regression_gate(output_dir: str | Path = ".loop/runs/regression-gate") -> dict[str, object]:
    """Run the four semantic contracts in stable order."""

    root = Path(output_dir).resolve()
    checks = [_benchmark_check(root), _sensitivity_check(root), _diagnostics_check(root), _repair_check(root)]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def main() -> None:
    result = run_regression_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
