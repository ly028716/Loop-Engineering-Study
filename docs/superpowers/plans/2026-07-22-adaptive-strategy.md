# Adaptive Strategy Experiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic adaptive-policy experiment that reaches its goal in fewer steps than a fixed policy while recovering from an injected action failure.

**Architecture:** Keep the experiment self-contained in `experiments/adaptive_strategy.py`. Four `Policy` implementations use the existing `LoopRunner`, `LoopTrace`, `MetricReport`, and Artifact functions. The adaptive policy records its selected mode in `Decision.parameters`, making strategy switches observable through existing `DECIDE` events.

**Tech Stack:** Python 3.11, project standard library code, pytest, existing `loop_engineering` package.

## Global Constraints

- Do not add third-party dependencies.
- Do not change the public interfaces in `loop_engineering/`.
- Persist one loadable Artifact per compared strategy under `.loop/runs/adaptive-strategy/`.
- Compare `fixed`, `error_aware`, `memory_aware`, and `adaptive` on the same deterministic scenario.
- The adaptive result must succeed in fewer steps than the fixed result and respect the configured safety budget.

---

## File Structure

- Create `experiments/adaptive_strategy.py`: deterministic action, four policies, experiment builder, Trace-derived counters, and JSON CLI.
- Create `tests/test_adaptive_strategy.py`: regression coverage for comparison order, success, step efficiency, recovery, decision observability, and Artifact round trips.
- Create `docs/adaptive-strategy.md`: learning guide explaining control signals, modes, metrics, and commands.
- Modify `docs/experiments.md`: add the script to the run sequence and link the guide.
- Modify `README.md` and `README.zh-CN.md`: add the experiment to learning navigation.
- Modify `docs/superpowers/sdd/progress.md`: record verified completion and test count.

### Task 1: Write the failing comparison tests

**Files:**
- Create: `tests/test_adaptive_strategy.py`
- Consumes: `experiments.adaptive_strategy.run_comparison`, `loop_engineering.artifacts.load_run_artifact`
- Produces: executable acceptance tests for the experiment module.

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from experiments.adaptive_strategy import run_comparison
from loop_engineering.artifacts import load_run_artifact


def test_adaptive_comparison_is_replayable_and_more_efficient(tmp_path: Path) -> None:
    results = run_comparison(tmp_path)
    by_strategy = {item["strategy"]: item for item in results}

    assert [item["strategy"] for item in results] == [
        "fixed", "error_aware", "memory_aware", "adaptive"
    ]
    assert all(item["success"] is True for item in results)
    assert by_strategy["adaptive"]["steps"] < by_strategy["fixed"]["steps"]
    assert by_strategy["adaptive"]["steps"] <= 8
    assert by_strategy["adaptive"]["switch_count"] >= 1
    assert by_strategy["adaptive"]["recovery_count"] >= 1

    for item in results:
        trace, report = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        assert report.steps == item["steps"]


def test_adaptive_trace_records_recovery_mode_after_failure(tmp_path: Path) -> None:
    result = next(item for item in run_comparison(tmp_path) if item["strategy"] == "adaptive")
    trace, _ = load_run_artifact(result["artifact_path"])

    failed_action_index = next(
        index
        for index, event in enumerate(trace.events)
        if event.phase == "ACT" and event.payload["success"] is False
    )
    later_modes = [
        event.payload["parameters"].get("mode")
        for event in trace.events[failed_action_index + 1 :]
        if event.phase == "DECIDE"
    ]
    assert "recovery" in later_modes
```

- [ ] **Step 2: Run the focused tests to verify failure**

Run: `python -m pytest tests/test_adaptive_strategy.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.adaptive_strategy'`.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_adaptive_strategy.py
git commit -m "test: define adaptive strategy expectations"
```

### Task 2: Implement the deterministic adaptive experiment

**Files:**
- Create: `experiments/adaptive_strategy.py`
- Test: `tests/test_adaptive_strategy.py`
- Consumes: `Action`, `ActionResult`, `NumericAction`, `GoalEvaluator`, `MetricReport`, `Feedback`, `LoopEvent`, `LoopState`, `LoopTrace`, `Decision`, `Policy`, `LoopRunner`, `MaxSteps`, `SuccessReached`.
- Produces: `build_experiment(strategy: str, output_dir: str | Path) -> tuple[LoopRunner, LoopState]` and `run_comparison(output_dir: str | Path = ".loop/runs/adaptive-strategy") -> list[dict[str, object]]`.

- [ ] **Step 1: Add bounded increment and deterministic action helpers**

```python
def _remaining_amount(state: LoopState, amount: float) -> float:
    return min(amount, max(state.goal - state.value, 0.0))


class FailOnSecondAction(Action):
    def __init__(self) -> None:
        self._failed = False
        self._numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if not self._failed and state.step == 1:
            self._failed = True
            return ActionResult(
                state=state.with_value(state.value, injected_failure=True),
                success=False,
                cost=0.0,
            )
        return self._numeric_action.apply(state, decision)
```

- [ ] **Step 2: Add the four policies and mode-aware adaptive selection**

```python
class AdaptivePolicy(Policy):
    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        remaining = state.goal - state.value
        failed = feedback.signals.get("action_success") is False
        if failed:
            mode, amount = "recovery", 1.0
        elif remaining <= 2.0:
            mode, amount = "careful", 1.0
        elif state.step >= 6:
            mode, amount = "budget_guard", 1.0
        else:
            mode, amount = "fast", 4.0
        return Decision(
            name="increment",
            parameters={"amount": _remaining_amount(state, amount), "mode": mode},
        )
```

Implement `FixedPolicy`, `ErrorAwarePolicy`, and `MemoryAwarePolicy` with the same `Policy.decide` signature. Their decisions must include only `amount`, allowing the result summary to report zero switch and recovery counts for non-adaptive strategies.

- [ ] **Step 3: Add an evaluator that exposes action failure to feedback**

```python
class RecoveryAwareEvaluator(Evaluator):
    def __init__(self) -> None:
        self._goal_evaluator = GoalEvaluator(tolerance=0.0)

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        evaluation = self._goal_evaluator.evaluate(before, result)
        return Evaluation(
            score=evaluation.score,
            success=evaluation.success,
            message=evaluation.message,
            signals={**evaluation.signals, "action_success": result.success},
        )
```

- [ ] **Step 4: Build runners and comparison summaries**

```python
def build_experiment(strategy: str, output_dir: str | Path) -> tuple[LoopRunner, LoopState]:
    del output_dir
    policies: dict[str, type[Policy]] = {
        "fixed": FixedPolicy,
        "error_aware": ErrorAwarePolicy,
        "memory_aware": MemoryAwarePolicy,
        "adaptive": AdaptivePolicy,
    }
    try:
        policy = policies[strategy]()
    except KeyError as error:
        raise ValueError(f"Unknown adaptive strategy: {strategy}") from error
    return (
        LoopRunner(
            policy=policy,
            action=FailOnSecondAction(),
            evaluator=RecoveryAwareEvaluator(),
            stop_conditions=[SuccessReached(), MaxSteps(8)],
        ),
        LoopState(step=0, value=0.0, goal=6.0),
    )
```

In `run_comparison`, iterate in the fixed order from Task 1, save `{strategy}.json`, and include `strategy`, `status`, `success`, `steps`, `final_score`, `switch_count`, `recovery_count`, `stop_reason`, and `artifact_path`. Derive the two counts from `DECIDE` event parameter `mode`; count changes between adjacent adaptive modes for `switch_count`, and count `mode == "recovery"` for `recovery_count`.

- [ ] **Step 5: Add the JSON command-line entry point**

```python
def main() -> None:
    print(json.dumps(run_comparison(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run focused tests and direct experiment**

Run: `python -m pytest tests/test_adaptive_strategy.py -q`

Expected: `2 passed`.

Run: `python experiments/adaptive_strategy.py`

Expected: JSON containing four results, with `adaptive.steps < fixed.steps`, `adaptive.recovery_count >= 1`, and four Artifact paths.

- [ ] **Step 7: Commit the implementation**

```bash
git add experiments/adaptive_strategy.py tests/test_adaptive_strategy.py
git commit -m "feat: add adaptive strategy experiment"
```

### Task 3: Document the experiment and verify the project

**Files:**
- Create: `docs/adaptive-strategy.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`
- Test: full suite and direct script command.
- Consumes: the public script and result fields from Task 2.
- Produces: learner-facing instructions and an updated project progress record.

- [ ] **Step 1: Write the learning guide**

Create `docs/adaptive-strategy.md` with these sections: `# 自适应策略与预算分配`, `## 学习目标`, `## 控制信号`, `## 四种策略`, `## 运行实验`, `## 阅读结果`, and `## 可继续探索的问题`. Explain the four adaptive modes, the deterministic failure injection, and the meaning of `steps`, `switch_count`, and `recovery_count`. Include this executable command:

```powershell
python experiments/adaptive_strategy.py
```

- [ ] **Step 2: Update experiment navigation and README files**

Add `python experiments/adaptive_strategy.py` after `failure_modes.py` in `docs/experiments.md`; add an `## 自适应策略与预算分配` section linking to `adaptive-strategy.md`. Add one learning-navigation link to `README.md` and one Chinese equivalent to `README.zh-CN.md`.

- [ ] **Step 3: Update progress after verification**

Replace the pending Phase 2 adaptive-strategy entry in `docs/superpowers/sdd/progress.md` with a statement naming the four strategies, Trace-based mode counters, the exact passing-test count, and four verified Artifacts.

- [ ] **Step 4: Run complete verification**

Run: `python -m pytest -q`

Expected: all tests pass, including `tests/test_adaptive_strategy.py`.

Run: `python experiments/adaptive_strategy.py`

Expected: four JSON results and four Artifact files in `.loop/runs/adaptive-strategy/`.

Run: `git diff --check`

Expected: exit code `0` with no whitespace errors.

- [ ] **Step 5: Commit documentation and progress**

```bash
git add docs/adaptive-strategy.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain adaptive strategy experiment"
```
