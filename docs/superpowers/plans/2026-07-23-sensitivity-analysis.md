# Sensitivity Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic single-parameter sensitivity experiment that identifies when four-policy rankings first change.

**Architecture:** `experiments/sensitivity_analysis.py` owns parameter configurations, parameterized failure actions, one-run scoring, stable ranking, and adjacent-value flip detection. It reuses existing policy classes, evaluator, Artifact APIs, and stopping primitives without modifying `loop_engineering/`.

**Tech Stack:** Python 3.11, project standard library modules, pytest.

## Global Constraints

- Do not add dependencies or change `loop_engineering/` public interfaces.
- Scan exactly three parameter families: `goal_distance=(4, 6, 8)`, `failure_attempt=(1, 2, 3)`, and `step_budget=(3, 5, 8)`.
- Baseline is goal `6`, failure attempt `2`, and budget `8`; each configuration changes only its declared parameter.
- Run four strategies for all 9 configurations and persist 36 loadable Artifacts under `.loop/runs/sensitivity-analysis/`.
- Rank by total score descending, steps ascending, then strategy name; rank starts at 1.

---

## File Structure

- Create `experiments/sensitivity_analysis.py`: configurations, actions, run scoring, ranking, flip analysis, JSON CLI.
- Create `tests/test_sensitivity_analysis.py`: matrix, parameter isolation, Artifact, ranking, and flip assertions.
- Create `docs/sensitivity-analysis.md`: learning guide.
- Modify `docs/experiments.md`, `README.md`, `README.zh-CN.md`, and `docs/superpowers/sdd/progress.md`.

### Task 1: Define sensitivity acceptance tests

**Files:**
- Create: `tests/test_sensitivity_analysis.py`
- Consumes: `experiments.sensitivity_analysis.run_sensitivity`, `loop_engineering.artifacts.load_run_artifact`
- Produces: executable acceptance tests for 9 configurations and 36 Artifacts.

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

from experiments.sensitivity_analysis import run_sensitivity
from loop_engineering.artifacts import load_run_artifact


def test_sensitivity_runs_nine_isolated_configurations(tmp_path: Path) -> None:
    result = run_sensitivity(tmp_path)

    assert len(result["configurations"]) == 9
    assert len(result["runs"]) == 36
    assert all(Path(item["artifact_path"]).exists() for item in result["runs"])
    for item in result["runs"]:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"

    for configuration in result["configurations"]:
        assert configuration["baseline"] == {"goal_distance": 6, "failure_attempt": 2, "step_budget": 8}
        assert len(configuration["runs"]) == 4
        assert len(configuration["artifact_paths"]) == 4
        values = configuration["parameters"]
        family = configuration["parameter_family"]
        assert values[family] == configuration["parameter_value"]
        for other in {"goal_distance", "failure_attempt", "step_budget"} - {family}:
            assert values[other] == {"goal_distance": 6, "failure_attempt": 2, "step_budget": 8}[other]


def test_sensitivity_ranking_and_flip_analysis_are_stable(tmp_path: Path) -> None:
    result = run_sensitivity(tmp_path)

    for configuration in result["configurations"]:
        ranking = configuration["ranking"]
        assert [item["rank"] for item in ranking] == [1, 2, 3, 4]
        assert ranking == sorted(ranking, key=lambda item: (-item["total_score"], item["steps"], item["strategy"]))
    assert set(result["flip_analysis"]) == {"goal_distance", "failure_attempt", "step_budget"}
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_sensitivity_analysis.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.sensitivity_analysis'`.

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_sensitivity_analysis.py
git commit -m "test: define sensitivity analysis expectations"
```

### Task 2: Implement parameter scan and flip analysis

**Files:**
- Create: `experiments/sensitivity_analysis.py`
- Test: `tests/test_sensitivity_analysis.py`
- Consumes: four policies and `RecoveryAwareEvaluator` from `experiments.adaptive_strategy`; existing Action, Artifact, MetricReport, LoopRunner, and stopping APIs.
- Produces: `run_sensitivity(output_dir: str | Path = ".loop/runs/sensitivity-analysis") -> dict[str, object]`.

- [ ] **Step 1: Define parameter constants and configurations**

```python
BASELINE = {"goal_distance": 6, "failure_attempt": 2, "step_budget": 8}
PARAMETER_VALUES = {
    "goal_distance": (4, 6, 8),
    "failure_attempt": (1, 2, 3),
    "step_budget": (3, 5, 8),
}

def _configurations() -> list[dict[str, object]]:
    return [
        {"parameter_family": family, "parameter_value": value,
         "parameters": {**BASELINE, family: value}}
        for family, values in PARAMETER_VALUES.items() for value in values
    ]
```

- [ ] **Step 2: Implement a parameterized failure action and one-run result**

```python
class FailOnAttemptAction(Action):
    def __init__(self, failure_attempt: int) -> None:
        self._failure_attempt = failure_attempt
        self._attempts = 0
        self._numeric_action = NumericAction()

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        self._attempts += 1
        if self._attempts == self._failure_attempt:
            return ActionResult(state=state.with_value(state.value, injected_failure=True), success=False, cost=0.0)
        return self._numeric_action.apply(state, decision)
```

For each strategy/configuration, create a fresh policy, `FailOnAttemptAction`, `RecoveryAwareEvaluator`, `SuccessReached`, and `MaxSteps(step_budget)`. Initial state uses `goal=float(goal_distance)`. Save `{family}-{value}--{strategy}.json`. Return `strategy`, `success`, `steps`, `final_score`, `failure_count`, `recovery_count`, `budget_respected`, and `artifact_path`.

- [ ] **Step 3: Implement deterministic scoring and ranking**

```python
def _score_runs(runs: list[dict[str, object]]) -> list[dict[str, object]]:
    best_steps = min(int(item["steps"]) for item in runs if item["success"])
    for item in runs:
        success_score = 50.0 if item["success"] else 0.0
        efficiency_score = 25.0 * best_steps / int(item["steps"]) if item["success"] else 0.0
        recovery_score = 15.0 if item["success"] and int(item["recovery_count"]) >= 1 else 0.0
        budget_score = 10.0 if item["budget_respected"] else 0.0
        item["total_score"] = success_score + efficiency_score + recovery_score + budget_score
    return sorted(runs, key=lambda item: (-float(item["total_score"]), int(item["steps"]), str(item["strategy"])))
```

After sorting, copy each entry and add `rank=index + 1`. If no policy succeeds, set every efficiency score to `0.0` rather than calling `min()`.

- [ ] **Step 4: Implement adjacent ranking comparison**

```python
def _flip_analysis(configurations: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    analysis = {}
    for family, values in PARAMETER_VALUES.items():
        ordered = sorted((item for item in configurations if item["parameter_family"] == family), key=lambda item: item["parameter_value"])
        flips = []
        for before, after in zip(ordered, ordered[1:]):
            before_order = {item["strategy"]: item["rank"] for item in before["ranking"]}
            after_order = {item["strategy"]: item["rank"] for item in after["ranking"]}
            for left, right in combinations(STRATEGIES, 2):
                if (before_order[left] < before_order[right]) != (after_order[left] < after_order[right]):
                    flips.append({"from_value": before["parameter_value"], "to_value": after["parameter_value"], "pair": [left, right]})
        analysis[family] = {"flips": flips, "no_flip": not flips}
    return analysis
```

- [ ] **Step 5: Implement public runner and CLI**

`run_sensitivity` builds the 9 configurations in the declaration order, runs all four strategies per configuration, stores `runs` globally, and stores each configuration’s `baseline`, local `runs`, `artifact_paths`, and `ranking`. Return `{"configurations": configurations, "runs": runs, "flip_analysis": _flip_analysis(configurations)}`. Add JSON `main()` and a `__main__` guard.

- [ ] **Step 6: Verify GREEN state and commit**

Run: `python -m pytest tests/test_sensitivity_analysis.py -q`

Expected: `2 passed`.

Run: `python experiments/sensitivity_analysis.py`

Expected: 9 configurations, 36 runs, 36 Artifact paths, and three flip-analysis records.

Run: `python -m pytest -q`

Expected: all tests pass.

```bash
git add experiments/sensitivity_analysis.py tests/test_sensitivity_analysis.py
git commit -m "feat: add sensitivity analysis experiment"
```

### Task 3: Document and verify sensitivity analysis

**Files:**
- Create: `docs/sensitivity-analysis.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Create learner documentation**

Use these exact headings: `# 参数敏感性分析`, `## 基线与参数族`, `## 运行实验`, `## 阅读排名翻转`, and `## 解释边界`. Document the 3 × 3 values, 9 configurations, 36 Artifacts, and the adjacent-value flip definition.

Create `docs/sensitivity-analysis.md` with headings `# 参数敏感性分析`, `## 基线与参数族`, `## 运行实验`, `## 阅读排名翻转`, and `## 解释边界`. Document the 3 × 3 values, 9 configurations, 36 Artifacts, adjacent-value flip definition, and this command:

```powershell
python experiments/sensitivity_analysis.py
```

- [ ] **Step 2: Update navigation and progress**

Add the sensitivity script after `benchmark_suite.py` in `docs/experiments.md`; add a guide link to both README learning paths; add an accurate progress entry naming 9 configurations, 36 Artifacts, and the final test count.

- [ ] **Step 3: Final verification and commit**

Run: `python -m pytest -q`

Expected: all tests pass.

Run: `python experiments/sensitivity_analysis.py`

Expected: 9 configurations, 36 run records, and flip analysis for each family.

Run: `git diff --check`

Expected: exit code `0`.

```bash
git add docs/sensitivity-analysis.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain sensitivity analysis experiment"
```
