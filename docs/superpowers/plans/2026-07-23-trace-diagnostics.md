# Trace Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic, Trace-only diagnostic findings and an executable four-case learning experiment.

**Architecture:** `loop_engineering/diagnostics.py` reads existing `LoopTrace` events without changing the runner or Artifact schema. `experiments/trace_diagnostics.py` composes existing experiment builders, saves Trace Artifacts and separate JSON reports, then exposes those findings to learning documentation.

**Tech Stack:** Python 3.11, standard-library dataclasses and JSON, pytest.

## Global Constraints

- Do not add dependencies or modify `LoopRunner`, policies, stopping conditions, or the Artifact JSON schema.
- Export only `DiagnosticFinding` and `diagnose_trace(trace, step_budget=None)` from the new diagnostic module.
- Emit only `action_failure`, `stalled_progress`, `budget_exhausted`, and `recovery_observed`, in stable declaration order.
- Derive stalled progress from the preceding `OBSERVE` value and the next `OBSERVE` value, or `trace.final_state.value` for the final iteration.
- Persist four Trace Artifacts and four separate JSON reports beneath `.loop/runs/trace-diagnostics/`.
- Keep recommendation strings fixed and evidence indices valid for the diagnosed Trace.

---

## File Structure

- Create `loop_engineering/diagnostics.py`: immutable finding model, event-index helpers, and four deterministic rules.
- Create `tests/test_diagnostics.py`: rule-level checks against real traces built by existing experiments.
- Create `experiments/trace_diagnostics.py`: four-case report runner and JSON CLI.
- Create `tests/test_trace_diagnostics.py`: Artifact/report persistence and complete label coverage.
- Create `docs/trace-diagnostics.md`: learner guide for labels, evidence, and limits.
- Modify `docs/experiments.md`, `README.md`, `README.zh-CN.md`, and `docs/superpowers/sdd/progress.md`.

### Task 1: Define diagnostic rule expectations

**Files:**
- Create: `tests/test_diagnostics.py`
- Consumes: existing `build_experiment` and `build_scenario` helpers.
- Produces: acceptance tests for all four `DiagnosticFinding.code` values and their evidence indices.

- [ ] **Step 1: Write the failing tests**

```python
from experiments.adaptive_strategy import build_experiment as build_adaptive_experiment
from experiments.benchmark_suite import build_scenario
from experiments.failure_modes import build_experiment as build_failure_experiment
from loop_engineering.diagnostics import diagnose_trace


def _trace_from(builder_result):
    runner, initial_state, *_ = builder_result
    return runner.run(initial_state)


def test_diagnose_trace_reports_failure_and_recovery_evidence(tmp_path) -> None:
    failure_trace = _trace_from(build_failure_experiment("action_failure", tmp_path))
    recovery_trace = _trace_from(build_adaptive_experiment("adaptive", tmp_path))

    failure = diagnose_trace(failure_trace)
    recovery = diagnose_trace(recovery_trace)

    assert [item.code for item in failure] == ["action_failure"]
    assert [item.code for item in recovery] == ["action_failure", "recovery_observed"]
    assert failure[0].recommendation == "Inspect feedback signals and choose a recovery action."
    assert recovery[1].severity == "info"
    assert all(item.evidence_event_indices for item in failure + recovery)


def test_diagnose_trace_reports_stall_and_budget_exhaustion() -> None:
    stalled_runner, stalled_state, stalled_budget = build_scenario("stalled_progress", "fixed")
    tight_runner, tight_state, tight_budget = build_scenario("tight_budget", "fixed")

    stalled = diagnose_trace(stalled_runner.run(stalled_state), stalled_budget)
    tight = diagnose_trace(tight_runner.run(tight_state), tight_budget)

    assert [item.code for item in stalled] == ["stalled_progress", "budget_exhausted"]
    assert [item.code for item in tight] == ["budget_exhausted"]
    assert stalled[1].severity == "error"
    assert all(index >= 0 for item in stalled + tight for index in item.evidence_event_indices)
    assert stalled == diagnose_trace(stalled_runner.run(stalled_state), stalled_budget)
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_diagnostics.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'loop_engineering.diagnostics'`.

- [ ] **Step 3: Commit the tests**

```bash
git add tests/test_diagnostics.py
git commit -m "test: define trace diagnostic expectations"
```

### Task 2: Implement Trace-only rule diagnostics

**Files:**
- Create: `loop_engineering/diagnostics.py`
- Test: `tests/test_diagnostics.py`
- Consumes: `LoopEvent`, `LoopTrace`, and `LoopState` from `loop_engineering.models`.
- Produces: `DiagnosticFinding` and `diagnose_trace(trace: LoopTrace, step_budget: int | None = None) -> list[DiagnosticFinding]`.

- [ ] **Step 1: Define the immutable finding contract and fixed messages**

```python
@dataclass(frozen=True)
class DiagnosticFinding:
    code: str
    severity: str
    message: str
    evidence_event_indices: tuple[int, ...]
    recommendation: str


_RULES = (
    ("action_failure", "warning", "One or more actions failed.", "Inspect feedback signals and choose a recovery action."),
    ("stalled_progress", "warning", "A successful action did not advance the state value.", "Inspect action semantics, progress signals, and no-progress stopping."),
    ("budget_exhausted", "error", "The run stopped at its step budget before success.", "Adjust the budget, action size, or early stopping strategy."),
    ("recovery_observed", "info", "A recovery decision followed an action failure.", "Compare recovery completion with its additional step cost."),
)
```

- [ ] **Step 2: Implement Trace index helpers**

```python
def _previous_observe_value(events: list[LoopEvent], action_index: int) -> float | None:
    for event in reversed(events[:action_index]):
        if event.phase == "OBSERVE" and "value" in event.payload:
            return float(event.payload["value"])
    return None


def _next_observe_value(trace: LoopTrace, action_index: int) -> float | None:
    for event in trace.events[action_index + 1 :]:
        if event.phase == "OBSERVE" and "value" in event.payload:
            return float(event.payload["value"])
    return trace.final_state.value if trace.final_state is not None else None
```

Create `_failure_indices`, `_stalled_indices`, `_budget_stop_index`, and `_recovery_evidence` helpers. A stalled index requires `ACT.success is True` and equal before/after values. `_budget_stop_index` returns the final event index only when the final event is `STOP`, its reason starts with `Reached maximum steps:`, and the final state status is not `SUCCEEDED`. `_recovery_evidence` returns the first failed `ACT` index plus the first later `DECIDE` index with `parameters.mode_code == 3.0`.

- [ ] **Step 3: Implement stable rule evaluation**

```python
def diagnose_trace(
    trace: LoopTrace,
    step_budget: int | None = None,
) -> list[DiagnosticFinding]:
    del step_budget
    findings: list[DiagnosticFinding] = []
    failure_indices = _failure_indices(trace.events)
    stalled_indices = _stalled_indices(trace)
    budget_index = _budget_stop_index(trace)
    recovery_indices = _recovery_evidence(trace.events, failure_indices)
    evidence_sets = (failure_indices, stalled_indices, budget_index, recovery_indices)
    for (code, severity, message, recommendation), evidence in zip(_RULES, evidence_sets):
        if evidence is not None and evidence != ():
            indices = (evidence,) if isinstance(evidence, int) else tuple(evidence)
            findings.append(DiagnosticFinding(code, severity, message, indices, recommendation))
    return findings
```

Use the fixed text from `_RULES`, tuple-convert every evidence sequence, and omit a finding when its rule has no evidence. The optional budget argument is accepted for the public contract but must not alter diagnosis because `STOP.reason` is the persisted evidence.

- [ ] **Step 4: Verify GREEN state and commit**

Run: `python -m pytest tests/test_diagnostics.py -q`

Expected: `2 passed`.

Run: `python -m pytest -q`

Expected: all existing tests plus the two new tests pass.

```bash
git add loop_engineering/diagnostics.py tests/test_diagnostics.py
git commit -m "feat: add trace diagnostics"
```

### Task 3: Add the four-case diagnostic experiment

**Files:**
- Create: `experiments/trace_diagnostics.py`
- Create: `tests/test_trace_diagnostics.py`
- Consumes: `diagnose_trace`, `save_run_artifact`, `build_experiment` from adaptive/failure modules, and `build_scenario` from benchmark suite.
- Produces: `run_diagnostics(output_dir: str | Path = ".loop/runs/trace-diagnostics") -> list[dict[str, object]]`.

- [ ] **Step 1: Write the failing integration test**

```python
import json
from pathlib import Path

from experiments.trace_diagnostics import run_diagnostics
from loop_engineering.artifacts import load_run_artifact


def test_trace_diagnostics_persists_four_cases_and_reports(tmp_path: Path) -> None:
    results = run_diagnostics(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure", "stalled_progress", "tight_budget", "adaptive_recovery",
    ]
    assert {finding["code"] for item in results for finding in item["findings"]} == {
        "action_failure", "stalled_progress", "budget_exhausted", "recovery_observed",
    }
    for item in results:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        report = json.loads(Path(item["report_path"]).read_text(encoding="utf-8"))
        assert report["case"] == item["case"]
        assert report["findings"] == item["findings"]
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_trace_diagnostics.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.trace_diagnostics'`.

- [ ] **Step 3: Implement scenario construction and persistence**

```python
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
```

For each case, run its fresh runner, save `{case}.artifact.json` through `save_run_artifact`, serialize `[asdict(finding) for finding in diagnose_trace(trace, budget)]` to `{case}.report.json` using UTF-8 and `ensure_ascii=False`, and return a record with `case`, `artifact_path`, `report_path`, `step_budget`, and `findings`. Add `main()` that prints `json.dumps(run_diagnostics(), ensure_ascii=False, indent=2)`.

- [ ] **Step 4: Verify GREEN state and commit**

Run: `python -m pytest tests/test_trace_diagnostics.py -q`

Expected: `1 passed`.

Run: `python experiments/trace_diagnostics.py`

Expected: four case records, four Artifact paths, four report paths, and all four diagnostic codes.

Run: `python -m pytest -q`

Expected: all tests pass.

```bash
git add experiments/trace_diagnostics.py tests/test_trace_diagnostics.py
git commit -m "feat: add trace diagnostics experiment"
```

### Task 4: Document and verify Trace diagnostics

**Files:**
- Create: `docs/trace-diagnostics.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`
- Consumes: the four fixed diagnostic codes and experiment command.
- Produces: documented learner path and accurate project progress.

- [ ] **Step 1: Create learner documentation**

Create `docs/trace-diagnostics.md` with headings `# Trace 诊断`, `## 运行实验`, `## 四类诊断与证据`, `## 阅读结构化报告`, and `## 解释边界`. Include this exact command:

```powershell
python experiments/trace_diagnostics.py
```

Document the four cases, the `code` / `severity` / `evidence_event_indices` / `recommendation` fields, the separate Artifact and report JSON files, and the fact that each finding is deterministic evidence rather than an LLM root-cause claim.

- [ ] **Step 2: Update navigation and progress**

Add `python experiments/trace_diagnostics.py` after `sensitivity_analysis.py` in `docs/experiments.md`. Add the Trace diagnostic guide after parameter sensitivity analysis in both README learning paths. Add one progress entry that names four cases, four Artifacts, four reports, and the actual final pytest count.

- [ ] **Step 3: Run final verification and commit**

Run: `python -m pytest -q`

Expected: all tests pass.

Run: `python experiments/trace_diagnostics.py`

Expected: four persisted Trace Artifacts and four persisted diagnostic reports.

Run: `git diff --check`

Expected: exit code `0`.

```bash
git add docs/trace-diagnostics.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain trace diagnostics experiment"
```
