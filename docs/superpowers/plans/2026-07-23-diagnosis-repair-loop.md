# Diagnosis Repair Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic Diagnose → Repair → Verify experiment that removes target Trace diagnostics through real reruns.

**Architecture:** `experiments/diagnosis_repair_loop.py` builds a baseline and a repaired runner for each of three cases, analyzes both with the existing `diagnose_trace`, and persists separate Artifacts plus one JSON report. It changes no runtime code, policies, diagnostic rules, or Artifact schema.

**Tech Stack:** Python 3.11, standard-library dataclasses and JSON, pytest.

## Global Constraints

- Do not add dependencies or modify `LoopRunner`, `diagnose_trace`, existing policies, or the Artifact schema.
- Run exactly `action_failure`, `stalled_progress`, and `tight_budget`, in that order.
- Use the declared deterministic repair mappings; do not search alternative repairs or modify historic traces.
- Persist two Artifacts and one UTF-8 JSON report per case beneath `.loop/runs/diagnosis-repair-loop/`.
- Set `repair_succeeded` only when the baseline has a target diagnostic, the repaired Trace succeeds, and repaired diagnostics have no target-code intersection.

---

## File Structure

- Create `experiments/diagnosis_repair_loop.py`: case mappings, baseline/repaired runners, summary construction, persistence, and JSON CLI.
- Create `tests/test_diagnosis_repair_loop.py`: three-case repair, diagnostics, Artifact, report, and repeatability assertions.
- Create `docs/diagnosis-repair-loop.md`: learner guide for the Diagnose → Repair → Verify process.
- Modify `docs/experiments.md`, `README.md`, `README.zh-CN.md`, and `docs/superpowers/sdd/progress.md`.

### Task 1: Define repair-loop acceptance tests

**Files:**
- Create: `tests/test_diagnosis_repair_loop.py`
- Consumes: `experiments.diagnosis_repair_loop.run_repair_loop`, `load_run_artifact`.
- Produces: test contract for three deterministic, evidence-backed repairs.

- [ ] **Step 1: Write the failing test**

```python
import json
from pathlib import Path

from experiments.diagnosis_repair_loop import run_repair_loop
from loop_engineering.artifacts import load_run_artifact


def test_repair_loop_eliminates_targets_and_persists_evidence(tmp_path: Path) -> None:
    results = run_repair_loop(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure", "stalled_progress", "tight_budget",
    ]
    assert all(item["repair_succeeded"] is True for item in results)
    for item in results:
        targets = set(item["target_diagnostic_codes"])
        assert targets & set(item["baseline"]["diagnostic_codes"])
        assert not targets & set(item["repaired"]["diagnostic_codes"])
        assert item["repaired"]["success"] is True

        for key in ("baseline_artifact_path", "repaired_artifact_path"):
            trace, _ = load_run_artifact(item[key])
            assert trace.events[-1].phase == "STOP"
        report = json.loads(Path(item["report_path"]).read_text(encoding="utf-8"))
        assert report == {key: value for key, value in item.items() if key != "report_path"}


def test_repair_loop_keeps_case_and_diagnostic_order_stable(tmp_path: Path) -> None:
    first = run_repair_loop(tmp_path / "first")
    second = run_repair_loop(tmp_path / "second")

    assert [item["case"] for item in first] == [item["case"] for item in second]
    assert [item["baseline"]["diagnostic_codes"] for item in first] == [
        item["baseline"]["diagnostic_codes"] for item in second
    ]
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_diagnosis_repair_loop.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.diagnosis_repair_loop'`.

- [ ] **Step 3: Commit the tests**

```bash
git add tests/test_diagnosis_repair_loop.py
git commit -m "test: define diagnosis repair loop expectations"
```

### Task 2: Implement real baseline/repaired reruns

**Files:**
- Create: `experiments/diagnosis_repair_loop.py`
- Test: `tests/test_diagnosis_repair_loop.py`
- Consumes: failure-mode `build_experiment`, benchmark `build_scenario`, `NumericAction`, `IncrementPolicy`, `GoalEvaluator`, `LoopRunner`, Artifact APIs, and `diagnose_trace`.
- Produces: `run_repair_loop(output_dir: str | Path = ".loop/runs/diagnosis-repair-loop") -> list[dict[str, object]]`.

- [ ] **Step 1: Declare case order and target diagnostics**

```python
CASES = ("action_failure", "stalled_progress", "tight_budget")
TARGET_CODES = {
    "action_failure": ("action_failure",),
    "stalled_progress": ("stalled_progress", "budget_exhausted"),
    "tight_budget": ("budget_exhausted",),
}
```

- [ ] **Step 2: Build baseline and repaired runners**

```python
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
```

The `steady_progress` repair is intentionally fresh: it replaces the stalled Action for `stalled_progress` and restores budget `8` for `tight_budget`.

- [ ] **Step 3: Summarize, persist, and verify one case**

```python
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
```

For each case, run both fresh runners, save `{case}.baseline.artifact.json` and `{case}.repaired.artifact.json` with `MetricReport.from_trace`, build both summaries, then calculate:

```python
targets = set(TARGET_CODES[case])
repair_succeeded = (
    bool(targets & set(baseline["diagnostic_codes"]))
    and bool(repaired["success"])
    and not (targets & set(repaired["diagnostic_codes"]))
)
```

Write the complete record except `report_path` as `{case}.report.json` with `ensure_ascii=False`, `indent=2`, UTF-8, and a trailing newline. Return the record plus the absolute `report_path`.

- [ ] **Step 4: Add public runner and CLI**

`run_repair_loop` resolves `output_dir`, processes `CASES` in declaration order, and returns the three records. Add `main()` that prints `json.dumps(run_repair_loop(), ensure_ascii=False, indent=2)` and a `__main__` guard. Use the same `_bootstrap.py` direct-script import convention as `trace_diagnostics.py`.

- [ ] **Step 5: Verify GREEN state and commit**

Run: `python -m pytest tests/test_diagnosis_repair_loop.py -q`

Expected: `2 passed`.

Run: `python experiments/diagnosis_repair_loop.py`

Expected: three records, six Artifact paths, three report paths, and `repair_succeeded: true` for every case.

Run: `python -m pytest -q`

Expected: all tests pass.

```bash
git add experiments/diagnosis_repair_loop.py tests/test_diagnosis_repair_loop.py
git commit -m "feat: add diagnosis repair loop experiment"
```

### Task 3: Document and verify the repair loop

**Files:**
- Create: `docs/diagnosis-repair-loop.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Create learner documentation**

Create `docs/diagnosis-repair-loop.md` with headings `# 诊断驱动修复闭环`, `## 运行实验`, `## 三个修复映射`, `## 判定修复成功`, and `## 解释边界`. Include this exact command:

```powershell
python experiments/diagnosis_repair_loop.py
```

Document the baseline/repair mapping for all three cases, six Artifact files, three report files, and the three required `repair_succeeded` conditions. State that this is a deterministic rule experiment rather than generic automatic repair.

- [ ] **Step 2: Update navigation and progress**

Add `python experiments/diagnosis_repair_loop.py` after `trace_diagnostics.py` in `docs/experiments.md`. Add the repair-loop guide after Trace diagnostics in both README learning paths. Add an accurate progress entry naming three cases, six Artifacts, three reports, and the final pytest count.

- [ ] **Step 3: Run final verification and commit**

Run: `python -m pytest -q`

Expected: all tests pass.

Run: `python experiments/diagnosis_repair_loop.py`

Expected: each repaired run succeeds and every target diagnostic is absent from its repaired summary.

Run: `git diff --check`

Expected: exit code `0`.

```bash
git add docs/diagnosis-repair-loop.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain diagnosis repair loop experiment"
```
