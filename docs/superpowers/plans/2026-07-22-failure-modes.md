# Failure Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现五种确定性失败模式的统一对比实验，并输出检测、恢复和停止结果。

**Architecture:** 新增实验专用的场景 Action、Evaluator 和 Policy，使用场景工厂创建隔离 Runner。结果分析从完成后的 `LoopTrace` 中计算失败次数、恢复尝试和证据冲突，并复用现有 Artifact 持久化。

**Tech Stack:** Python 3.11+, dataclasses, pytest, UTF-8 JSON, Markdown。

## Global Constraints

- 不修改 `LoopRunner`、Artifact 格式和现有实验行为。
- 五种场景都使用本地确定性组件，不访问网络、LLM、数据库或外部服务。
- 每个场景独立创建 Runner 和状态。
- 运行产物只能写入 `.loop/runs/failure-modes/`，不得提交到 Git。
- 新增行为先写测试；完整 pytest 必须继续通过。

---

### Task 1: Add failure-mode tests

**Files:**
- Create: `tests/test_failure_modes.py`

**Interfaces:**
- Tests consume `run_comparison(output_dir)` from `experiments.failure_modes`.

- [ ] **Step 1: Write the scenario result contract test**

```python
def test_run_comparison_returns_all_failure_modes(tmp_path):
    results = run_comparison(tmp_path)
    assert [item["failure_mode"] for item in results] == [
        "action_failure",
        "evaluator_disagreement",
        "missing_feedback",
        "oscillation",
        "safety_limit",
    ]
    assert all(Path(item["artifact_path"]).exists() for item in results)
```

- [ ] **Step 2: Write detection and outcome assertions**

```python
def test_failure_modes_have_expected_detection_and_stopping(tmp_path):
    results = {item["failure_mode"]: item for item in run_comparison(tmp_path)}
    assert results["action_failure"]["success"] is True
    assert results["action_failure"]["recovery_attempts"] >= 1
    assert results["evaluator_disagreement"]["evidence_conflicts"] == 1
    assert results["missing_feedback"]["failure_count"] >= 1
    assert results["oscillation"]["stop_reason"] == "Reached maximum steps: 6"
    assert results["safety_limit"]["stop_reason"] == "Reached maximum steps: 3"
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_failure_modes.py -q`

Expected: FAIL during collection because `experiments.failure_modes` does not exist.

### Task 2: Implement the unified failure-mode experiment

**Files:**
- Create: `experiments/failure_modes.py`

**Interfaces:**
- `run_comparison(output_dir) -> list[dict[str, object]]`
- `build_experiment(failure_mode, output_dir) -> tuple[LoopRunner, LoopState]`

- [ ] **Step 1: Implement deterministic scenario components**

Implement a fail-once Action, always-failing Action, stalled/oscillating Actions,
retry-aware Evaluator, silent-failure Evaluator, and faulty Evaluator. Keep all
components local to the experiment module and make each scenario's trigger explicit.

- [ ] **Step 2: Implement five scenario configurations**

Use goal `3.0`. `action_failure` uses retry feedback and succeeds;
`evaluator_disagreement` reaches the goal but uses a faulty evaluator and
`MaxSteps(1)`; `missing_feedback` uses a silent failure evaluator and a
conservative increment policy; `oscillation` uses `MaxSteps(6)`; `safety_limit`
uses an always-failing action and `MaxSteps(3)`.

- [ ] **Step 3: Implement Trace-based result analysis**

Count failed `ACT` events, later `DECIDE` events after a failure, and conflicts
where an action succeeds at the goal while evaluation reports failure. Persist
each trace and return the complete result contract with absolute Artifact paths.

- [ ] **Step 4: Run focused tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_failure_modes.py -q`

Expected: all scenario and result-analysis tests pass.

### Task 3: Add learning documentation and navigation

**Files:**
- Create: `docs/failure-modes.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Document the failure matrix**

Explain each trigger, detection evidence, recovery behavior, expected stop
reason, and the limits of the deterministic experiment.

- [ ] **Step 2: Add run and Artifact inspection commands**

Document `python experiments/failure_modes.py` and show how to inspect failed
ACT events and evidence conflicts from an Artifact.

- [ ] **Step 3: Update navigation and progress**

Add the document to both README learning paths and the experiment index; record
the completed phase in the progress ledger.

- [ ] **Step 4: Run documentation check**

Run: `git diff --check`

Expected: no whitespace errors.

### Task 4: Full verification and commit

- [ ] **Step 1: Run full tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q`

Expected: all previous 51 tests plus the new failure-mode tests pass.

- [ ] **Step 2: Run the direct experiment**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/failure_modes.py`

Expected: five JSON records with the configured detection and stopping outcomes.

- [ ] **Step 3: Verify ignored outputs and status**

Run: `git check-ignore .loop/runs/failure-modes/*.json` and
`git status --short --branch`.

- [ ] **Step 4: Commit**

```powershell
git add experiments/failure_modes.py tests/test_failure_modes.py docs/failure-modes.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md docs/superpowers/plans/2026-07-22-failure-modes.md
git commit -m "feat: add failure modes experiment"
```
