# Feedback Strategy Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现三个确定性的反馈策略对比实验，并用测试、Trace、Artifact 和文档展示反馈与记忆如何影响循环决策。

**Architecture:** 新增实验专用策略和一次性失败动作，复用现有 `LoopRunner`、`NumericAction`、`GoalEvaluator`、`MetricReport` 与 Artifact API。实验脚本为每个策略创建隔离 Runner，输出统一 JSON 结果并分别保存 Artifact；现有运行时接口保持不变。

**Tech Stack:** Python 3.11+, dataclasses, pytest, UTF-8 JSON, Markdown。

## Global Constraints

- 不修改 `LoopRunner`、Artifact 格式和现有 CLI 行为。
- 三种策略使用相同的初始状态、Evaluator 和停止条件。
- 实验不访问网络、不使用 LLM、数据库或外部服务。
- 运行产物只能写入 `.loop/runs/feedback-strategies/`，不得提交到 Git。
- 新增行为必须先有测试，再实现；完整测试必须继续通过。

---

### Task 1: Add strategy behavior tests

**Files:**
- Create: `tests/test_feedback_strategies.py`

**Interfaces:**
- Tests will consume `FixedIncrementPolicy`, `ErrorAwarePolicy`, `MemoryAwarePolicy`, `FailOnceAction`, `build_experiment`, and `run_comparison` from `experiments.feedback_strategies`.

- [ ] **Step 1: Write tests for decisions and comparison results**

```python
def test_error_aware_policy_uses_absolute_error_feedback():
    policy = ErrorAwarePolicy()
    state = LoopState(step=1, value=1.0, goal=6.0)
    decision = policy.decide(
        state,
        Feedback(score=0.2, message="not reached", signals={"absolute_error": 5.0}),
    )
    assert decision.parameters["amount"] == 2.0


def test_memory_aware_policy_reacts_to_failed_action_event():
    policy = MemoryAwarePolicy()
    state = LoopState(step=1, value=0.0, goal=6.0)
    history = [LoopEvent(step=1, phase="ACT", payload={"success": False, "cost": 0.0})]
    assert policy.decide(state, Feedback.empty(), history).parameters["amount"] == 2.0


def test_run_comparison_returns_three_replayable_results(tmp_path):
    results = run_comparison(tmp_path)
    assert [item["strategy"] for item in results] == ["fixed", "error_aware", "memory_aware"]
    assert all(item["success"] for item in results)
    assert all(Path(item["artifact_path"]).exists() for item in results)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_feedback_strategies.py -q`

Expected: FAIL because `experiments.feedback_strategies` does not exist.

### Task 2: Implement the deterministic comparison experiment

**Files:**
- Create: `experiments/feedback_strategies.py`

**Interfaces:**
- `FixedIncrementPolicy.decide(state, feedback, recent_events=None) -> Decision`
- `ErrorAwarePolicy.decide(state, feedback, recent_events=None) -> Decision`
- `MemoryAwarePolicy.decide(state, feedback, recent_events=None) -> Decision`
- `FailOnceAction.apply(state, decision) -> ActionResult`
- `build_experiment(strategy, output_dir) -> tuple[LoopRunner, LoopState]`
- `run_comparison(output_dir) -> list[dict[str, object]]`

- [ ] **Step 1: Implement fixed, error-aware, and memory-aware policies**

The fixed policy always selects `amount=1.0`. The error-aware policy selects
`amount=2.0` when `feedback.signals["absolute_error"] > 1.0`, otherwise `1.0`.
The memory-aware policy selects `amount=2.0` when the recent events contain a
failed `ACT` or two consecutive `EVALUATE` events with no score improvement,
otherwise `1.0`.

- [ ] **Step 2: Implement the isolated failure action and runner factory**

`FailOnceAction` returns `success=False` without changing value on its first
call, then delegates to `NumericAction`. `build_experiment("memory_aware", ...)`
uses this action; the other strategies use `NumericAction` directly. All
strategies use goal `6.0`, `GoalEvaluator(0.0)`, `SuccessReached()`, and
`MaxSteps(10)`.

- [ ] **Step 3: Implement Artifact persistence and JSON summary output**

`run_comparison()` creates one subdirectory per strategy, saves each trace with
`save_run_artifact()`, derives `MetricReport.from_trace()`, and returns records
with `strategy`, all metric fields, `stop_reason`, and absolute `artifact_path`.
The direct script entry point prints one JSON array and supports the existing
direct-script import bootstrap convention.

- [ ] **Step 4: Run focused tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_feedback_strategies.py -q`

Expected: PASS for all new strategy and artifact tests.

### Task 3: Add learning documentation and navigation

**Files:**
- Create: `docs/feedback-strategies.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: Document the experiment question and controlled variables**

Explain the baseline, feedback-aware and memory-aware strategies, common
Evaluator/stop conditions, expected observations, and how to interpret steps,
score, cost, and stop reason.

- [ ] **Step 2: Add commands and Artifact inspection examples**

Document `python experiments/feedback_strategies.py` and show how to load one
result with `load_run_artifact()`.

- [ ] **Step 3: Add both language README links**

Add the new document to the learning path without claiming general Agent or LLM
performance.

- [ ] **Step 4: Check documentation consistency**

Run: `git diff --check`

Expected: no whitespace errors.

### Task 4: Full verification and integration

**Files:**
- Modify: `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Run the complete test suite**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q`

Expected: existing 41 tests plus the new strategy tests pass.

- [ ] **Step 2: Run the direct experiment**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/feedback_strategies.py`

Expected: a JSON array with three strategy records and three artifact paths.

- [ ] **Step 3: Verify the worktree**

Run: `git status --short --branch` and confirm only intended source, test, doc,
plan, and progress files are staged; `.loop/runs` remains ignored.

- [ ] **Step 4: Commit**

```powershell
git add experiments/feedback_strategies.py tests/test_feedback_strategies.py docs/feedback-strategies.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md docs/superpowers/plans/2026-07-22-feedback-strategy-comparison.md
git commit -m "feat: add feedback strategy comparison experiment"
```
