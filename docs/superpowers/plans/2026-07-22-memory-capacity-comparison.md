# Memory Capacity Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `no_memory`、`short_memory`、`working_memory` 和 `long_window` 四种记忆容量配置的确定性对比实验。

**Architecture:** 新增实验专用的失败计划动作和记忆恢复策略，复用现有 `LoopRunner`、`WorkingMemory`、`GoalEvaluator`、`MetricReport` 和 Artifact API。每个记忆配置单独创建 Runner，统一运行两次计划失败并输出 JSON 结果；现有运行时接口不变。

**Tech Stack:** Python 3.11+, dataclasses, collections.deque, pytest, UTF-8 JSON, Markdown。

## Global Constraints

- 不修改 `LoopRunner`、`WorkingMemory`、Artifact 格式和现有 CLI 行为。
- 四种配置共享初始状态、失败计划、Evaluator 和停止条件。
- 失败计划只在第 1 次和第 4 次 Action 调用失败。
- 运行产物只能写入 `.loop/runs/memory-capacity/`，不得提交到 Git。
- 新增行为先写测试；完整 pytest 必须继续通过。

---

### Task 1: Add memory capacity tests

**Files:**
- Create: `tests/test_memory_capacity.py`

**Interfaces:**
- Tests consume `FailureScheduleAction`, `MemoryRecoveryPolicy`, `build_experiment`, and `run_comparison` from `experiments.memory_capacity`.

- [ ] **Step 1: Write failure-plan and policy tests**

```python
def test_failure_schedule_fails_only_on_calls_one_and_four():
    action = FailureScheduleAction(failure_calls={1, 4})
    state = LoopState(step=0, value=0.0, goal=6.0)
    decision = Decision(name="increment", parameters={"amount": 1.0})

    results = [action.apply(state, decision) for _ in range(4)]

    assert [result.success for result in results] == [False, True, True, False]


def test_memory_recovery_policy_reacts_to_failed_action():
    policy = MemoryRecoveryPolicy()
    state = LoopState(step=1, value=0.0, goal=6.0)
    history = [LoopEvent(step=1, phase="ACT", payload={"success": False, "cost": 0.0})]

    decision = policy.decide(state, Feedback.empty(), history)

    assert decision.parameters["amount"] == 2.0
```

- [ ] **Step 2: Write comparison and Artifact tests**

```python
def test_run_comparison_returns_all_memory_modes(tmp_path):
    results = run_comparison(tmp_path)

    assert [item["memory_mode"] for item in results] == [
        "no_memory", "short_memory", "working_memory", "long_window"
    ]
    assert all(item["success"] for item in results)
    assert all(Path(item["artifact_path"]).exists() for item in results)
    assert all(item["failure_count"] == 2 for item in results)
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_memory_capacity.py -q`

Expected: FAIL during collection because `experiments.memory_capacity` does not exist.

### Task 2: Implement the memory capacity experiment

**Files:**
- Create: `experiments/memory_capacity.py`

**Interfaces:**
- `FailureScheduleAction(failure_calls: set[int]).apply(state, decision) -> ActionResult`
- `MemoryRecoveryPolicy.decide(state, feedback, recent_events=None) -> Decision`
- `build_experiment(memory_mode, output_dir) -> tuple[LoopRunner, LoopState, int]`
- `run_comparison(output_dir) -> list[dict[str, object]]`

- [ ] **Step 1: Implement the scheduled failure Action**

Track one-based Action call count. If the count is in `{1, 4}`, return
`ActionResult(state.with_value(state.value, scheduled_failure=True), False, 0.0)`;
otherwise delegate to `NumericAction`.

- [ ] **Step 2: Implement memory-aware and no-memory policy behavior**

`MemoryRecoveryPolicy` selects `amount=2.0` when recent events contain a failed
`ACT`, otherwise `1.0`. A `no_memory` flag causes the same policy to ignore its
`recent_events` argument, keeping the comparison focused on visibility.

- [ ] **Step 3: Implement configuration factory and result collection**

Use capacities `{no_memory: 1, short_memory: 7, working_memory: 21,
long_window: 1000}`. Each configuration uses goal `6.0`,
`GoalEvaluator(tolerance=0.0)`, `SuccessReached()`, and `MaxSteps(12)`. Persist
each trace and return metrics plus `failure_count`, `recovery_action_count`,
`stop_reason`, and absolute `artifact_path`.

- [ ] **Step 4: Run focused tests**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_memory_capacity.py -q`

Expected: PASS for scheduled failures, policy visibility, four configurations,
and Artifact paths.

### Task 3: Add learning documentation and navigation

**Files:**
- Create: `docs/memory-capacity.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: Explain event-window capacity**

Document why capacities are event counts, how the four modes differ, and why
the no-memory baseline is necessary.

- [ ] **Step 2: Document commands and inspection**

Add `python experiments/memory_capacity.py` and a `load_run_artifact()` example
that filters failed `ACT` events.

- [ ] **Step 3: Add README navigation links**

Link the new document from both language READMEs and the experiment index.

- [ ] **Step 4: Run documentation checks**

Run: `git diff --check`

Expected: no whitespace errors.

### Task 4: Verify and commit

**Files:**
- Modify: `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Run the full suite**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q`

Expected: existing 44 tests plus the memory tests pass.

- [ ] **Step 2: Run the direct experiment**

Run: `C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/memory_capacity.py`

Expected: four JSON result records and four ignored Artifact files.

- [ ] **Step 3: Verify ignored outputs and worktree**

Run: `git check-ignore .loop/runs/memory-capacity/*.json` and
`git status --short --branch`.

- [ ] **Step 4: Commit**

```powershell
git add experiments/memory_capacity.py tests/test_memory_capacity.py docs/memory-capacity.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md docs/superpowers/plans/2026-07-22-memory-capacity-comparison.md
git commit -m "feat: add memory capacity comparison experiment"
```
