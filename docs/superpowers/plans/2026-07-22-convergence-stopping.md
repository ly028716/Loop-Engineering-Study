# Convergence and Stopping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `NoProgress` 停止条件，并实现收敛、停滞、振荡三种模式的可回放对比实验。

**Architecture:** `NoProgress` 作为现有 `StopCondition` 的独立实现，只读取历史 `EVALUATE` 事件，不修改 Runner。实验脚本通过三种专用 Action/Policy 配置复用同一个 Runner、Evaluator、Artifact 和指标边界。

**Tech Stack:** Python 3.11+, dataclasses, pytest, UTF-8 JSON, Markdown。

## Global Constraints

- 保持 `SuccessReached`、`MaxSteps`、`LoopRunner` 和 Artifact 格式兼容。
- `NoProgress` 只判断近期评估是否有足够的得分提升，不判断目标是否达成。
- 三种实验模式不得访问网络、LLM、数据库或外部服务。
- 运行产物只能写入 `.loop/runs/convergence-stopping/`，不得提交到 Git。
- 新增行为先写测试；完整 pytest 必须继续通过。

---

### Task 1: Add `NoProgress` tests

**Files:**
- Modify: `tests/test_stopping.py`

**Interfaces:**
- Tests consume `NoProgress(window, min_score_gain)` from `loop_engineering.stopping`.

- [ ] **Step 1: Write validation and behavior tests**

```python
def test_no_progress_rejects_invalid_configuration():
    with pytest.raises(ValueError, match="window must be at least 1"):
        NoProgress(window=0)
    with pytest.raises(ValueError, match="min_score_gain cannot be negative"):
        NoProgress(window=2, min_score_gain=-0.1)


def test_no_progress_waits_for_window_and_stops_on_flat_scores():
    condition = NoProgress(window=3)
    history = [
        LoopEvent(step=1, phase="EVALUATE", payload={"score": 0.5}),
        LoopEvent(step=2, phase="EVALUATE", payload={"score": 0.5}),
        LoopEvent(step=3, phase="EVALUATE", payload={"score": 0.5}),
    ]
    decision = condition.should_stop(
        LoopState(step=3, value=0.0, goal=1.0), evaluation(success=False), history
    )
    assert decision.stop is True
    assert decision.reason == "No progress for 3 evaluations"


def test_no_progress_continues_when_score_improves():
    condition = NoProgress(window=3)
    history = [
        LoopEvent(step=1, phase="EVALUATE", payload={"score": 0.2}),
        LoopEvent(step=2, phase="EVALUATE", payload={"score": 0.4}),
        LoopEvent(step=3, phase="EVALUATE", payload={"score": 0.5}),
    ]
    assert condition.should_stop(
        LoopState(step=3, value=2.0, goal=3.0), evaluation(success=False), history
    ).stop is False
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_stopping.py -q`

Expected: FAIL because `NoProgress` is not defined.

### Task 2: Implement `NoProgress`

**Files:**
- Modify: `loop_engineering/stopping.py`
- Modify: `tests/test_stopping.py`

- [ ] **Step 1: Implement configuration validation**

Reject `window < 1` and `min_score_gain < 0.0` with the exact messages used by
the tests.

- [ ] **Step 2: Implement recent score gain detection**

Read only `EVALUATE` events with a numeric `score`. Return `stop=False` when
fewer than `window` scores exist. For the latest `window` scores, stop only if
every adjacent gain is less than or equal to `min_score_gain`.

- [ ] **Step 3: Run stopping tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_stopping.py -q`

Expected: all stopping tests pass.

### Task 3: Add convergence comparison experiment

**Files:**
- Create: `experiments/convergence_stopping.py`
- Create: `tests/test_convergence_stopping.py`

**Interfaces:**
- `build_experiment(mode, output_dir) -> tuple[LoopRunner, LoopState]`
- `run_comparison(output_dir) -> list[dict[str, object]]`

- [ ] **Step 1: Write experiment tests**

```python
def test_run_comparison_has_expected_stop_reasons(tmp_path):
    results = run_comparison(tmp_path)
    by_mode = {item["mode"]: item for item in results}
    assert by_mode["converging"]["success"] is True
    assert by_mode["stalled"]["stop_reason"] == "No progress for 3 evaluations"
    assert by_mode["oscillating"]["stop_reason"] == "Reached maximum steps: 6"
    assert all(Path(item["artifact_path"]).exists() for item in results)
```

- [ ] **Step 2: Run experiment tests and verify they fail**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_convergence_stopping.py -q`

Expected: FAIL during collection because the experiment module does not exist.

- [ ] **Step 3: Implement the three deterministic modes**

Use goal `3.0` and `MaxSteps(6)`. `converging` uses `NumericAction` and
`IncrementPolicy(1.0)` with `SuccessReached` first. `stalled` uses an action that
keeps value unchanged and `[SuccessReached(), NoProgress(3), MaxSteps(6)]`.
`oscillating` alternates `+1.0` and `-1.0` while using
`[SuccessReached(), NoProgress(3), MaxSteps(6)]`; its scores rise and fall, so
`NoProgress` does not trigger.

- [ ] **Step 4: Persist artifacts and return unified results**

Save one Artifact per mode and include `mode`, `steps`, `final_score`, `success`,
`score_history`, `stop_reason`, and absolute `artifact_path`.

- [ ] **Step 5: Run focused experiment tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_convergence_stopping.py -q`

Expected: all experiment tests pass and Artifacts load successfully.

### Task 4: Add learning documentation and integrate

**Files:**
- Create: `docs/convergence-stopping.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Document convergence and stop reasons**

Explain the three modes, `NoProgress` semantics, and why no-progress and
max-step stops are different from success.

- [ ] **Step 2: Add run and Artifact inspection commands**

Document `python experiments/convergence_stopping.py` and a
`load_run_artifact()` example.

- [ ] **Step 3: Update navigation and progress**

Link the new document from both READMEs and the experiment index; record the
completed phase in the progress ledger.

- [ ] **Step 4: Run documentation check**

Run: `git diff --check`

Expected: no whitespace errors.

### Task 5: Full verification and commit

- [ ] **Step 1: Run full tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q`

Expected: all previous 47 tests plus the new convergence tests pass.

- [ ] **Step 2: Run the direct experiment**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/convergence_stopping.py`

Expected: three JSON results with distinct stop reasons.

- [ ] **Step 3: Verify ignored outputs and status**

Run: `git check-ignore .loop/runs/convergence-stopping/*.json` and
`git status --short --branch`.

- [ ] **Step 4: Commit**

```powershell
git add loop_engineering/stopping.py tests/test_stopping.py experiments/convergence_stopping.py tests/test_convergence_stopping.py docs/convergence-stopping.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md docs/superpowers/plans/2026-07-22-convergence-stopping.md
git commit -m "feat: add convergence stopping experiment"
```
