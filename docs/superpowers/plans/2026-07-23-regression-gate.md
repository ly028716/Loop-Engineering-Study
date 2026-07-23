# Regression Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic semantic regression gate for benchmark, sensitivity, diagnostics, and repair-loop capabilities.

**Architecture:** `experiments/regression_gate.py` invokes the four existing public experiment functions in dedicated child directories and converts their results into four stable checks. The CLI prints checks and exits nonzero when any contract fails; no existing runtime or Artifact schema changes.

**Tech Stack:** Python 3.11, standard library, pytest.

## Global Constraints

- Add no dependency and do not change existing experiment APIs, `LoopRunner`, diagnostics, policies, or Artifact schema.
- Check order is `benchmark`, `sensitivity`, `diagnostics`, `repair_loop`.
- Each check has non-empty `name`, boolean `passed`, and non-empty `evidence`.
- All child experiment outputs are under `.loop/runs/regression-gate/` by default.

---

### Task 1: Define gate acceptance tests

**Files:**
- Create: `tests/test_regression_gate.py`
- Produces: contract for passing checks, stable order, evidence, and child outputs.

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

from experiments.regression_gate import run_regression_gate


def test_regression_gate_preserves_all_semantic_contracts(tmp_path: Path) -> None:
    result = run_regression_gate(tmp_path)

    assert result["passed"] is True
    assert [item["name"] for item in result["checks"]] == [
        "benchmark", "sensitivity", "diagnostics", "repair_loop",
    ]
    assert all(item["passed"] is True and item["evidence"] for item in result["checks"])
    assert all((tmp_path / name).exists() for name in ("benchmark", "sensitivity", "diagnostics", "repair-loop"))
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_regression_gate.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.regression_gate'`.

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_regression_gate.py
git commit -m "test: define regression gate expectations"
```

### Task 2: Implement semantic checks and CLI

**Files:**
- Create: `experiments/regression_gate.py`
- Test: `tests/test_regression_gate.py`
- Consumes: `run_benchmark`, `run_sensitivity`, `run_diagnostics`, `run_repair_loop`.
- Produces: `run_regression_gate(output_dir: str | Path = ".loop/runs/regression-gate") -> dict[str, object]`.

- [ ] **Step 1: Define a stable check helper**

```python
def _check(name: str, passed: bool, evidence: str) -> dict[str, object]:
    return {"name": name, "passed": passed, "evidence": evidence}
```

- [ ] **Step 2: Implement the four checks**

```python
benchmark = run_benchmark(root / "benchmark")
scores = {item["strategy"]: item["total_score"] for item in benchmark["summaries"]}
benchmark_check = _check(
    "benchmark",
    len(benchmark["runs"]) == 20 and len(benchmark["summaries"]) == 4 and scores["adaptive"] > scores["fixed"],
    f"runs={len(benchmark['runs'])}; adaptive={scores['adaptive']}; fixed={scores['fixed']}",
)
```

For sensitivity, require 9 configurations, 36 runs, every non-family parameter equals its configuration baseline, and `flip_analysis["goal_distance"]["no_flip"] is True`. For diagnostics, require four records, the union of finding codes equals the four declared codes, and every `artifact_path` and `report_path` exists. For repair loop, require three records and every record has `repair_succeeded is True`, repaired success, and no intersection between `target_diagnostic_codes` and repaired diagnostic codes.

- [ ] **Step 3: Add public runner and nonzero failure exit**

```python
def run_regression_gate(output_dir: str | Path = ".loop/runs/regression-gate") -> dict[str, object]:
    root = Path(output_dir).resolve()
    checks = [_benchmark_check(root), _sensitivity_check(root), _diagnostic_check(root), _repair_check(root)]
    return {"passed": all(item["passed"] for item in checks), "checks": checks}


def main() -> None:
    result = run_regression_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
```

Use the existing `_bootstrap.py` direct-script import convention. Do not catch child-experiment exceptions.

- [ ] **Step 4: Verify GREEN state and commit**

Run: `python -m pytest tests/test_regression_gate.py -q`

Expected: `1 passed`.

Run: `python experiments/regression_gate.py`

Expected: four passing checks and exit code `0`.

Run: `python -m pytest -q`

Expected: all tests pass.

```bash
git add experiments/regression_gate.py tests/test_regression_gate.py
git commit -m "feat: add semantic regression gate"
```

### Task 3: Document and verify the gate

**Files:**
- Create: `docs/regression-gate.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Document the gate**

Create `docs/regression-gate.md` with headings `# 回归门禁`, `## 运行门禁`, `## 四组语义契约`, and `## 解释边界`, documenting this command:

```powershell
python experiments/regression_gate.py
```

Explain the four checks, evidence strings, child-output directories, and nonzero failure exit; distinguish semantic contracts from snapshots and performance benchmarks.

- [ ] **Step 2: Update navigation, verify, and commit**

Add the script after `diagnosis_repair_loop.py` in `docs/experiments.md`, add the guide after the repair loop in both READMEs, and record the final pytest count in progress. Run `python -m pytest -q`, `python experiments/regression_gate.py`, and `git diff --check`, then commit:

```bash
git add docs/regression-gate.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain regression gate experiment"
```
