# Benchmark Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic 5-scenario benchmark that scores and ranks four loop policies with replayable evidence.

**Architecture:** `experiments/benchmark_suite.py` owns scenario construction, per-run Trace extraction, aggregation, scoring, and ranking. It reuses existing actions, evaluators, Artifact persistence, and the four policy classes from `experiments/adaptive_strategy.py`; it does not modify the core loop package.

**Tech Stack:** Python 3.11, existing project standard library modules, pytest.

## Global Constraints

- Do not add third-party dependencies or change `loop_engineering/` public interfaces.
- Run exactly `fixed`, `error_aware`, `memory_aware`, and `adaptive` over exactly `steady_progress`, `action_failure`, `missing_feedback`, `stalled_progress`, and `tight_budget`, in that order.
- Persist 20 loadable Artifacts under `.loop/runs/benchmark-suite/`.
- Total score is 0–100: success 50, efficiency 25, recovery 15, budget 10.
- Rank by total score descending, average successful steps ascending, then strategy name ascending.

---

## File Structure

- Create `experiments/benchmark_suite.py`: scenario factories, benchmark runner, metrics, scoring, ranking, CLI.
- Create `tests/test_benchmark_suite.py`: scenario/Artifact, score/ranking, and deterministic comparison tests.
- Create `docs/benchmark-suite.md`: learner guide for the matrix and scoring.
- Modify `docs/experiments.md`, `README.md`, `README.zh-CN.md`, and `docs/superpowers/sdd/progress.md`.

### Task 1: Define benchmark-facing tests

**Files:**
- Create: `tests/test_benchmark_suite.py`
- Consumes: `experiments.benchmark_suite.run_benchmark`, `loop_engineering.artifacts.load_run_artifact`
- Produces: acceptance coverage for the 20 run records and stable ranking.

- [ ] **Step 1: Write failing acceptance tests**

```python
from pathlib import Path

from experiments.benchmark_suite import run_benchmark
from loop_engineering.artifacts import load_run_artifact


def test_benchmark_runs_matrix_and_persists_artifacts(tmp_path: Path) -> None:
    result = run_benchmark(tmp_path)

    assert result["scenarios"] == [
        "steady_progress", "action_failure", "missing_feedback",
        "stalled_progress", "tight_budget",
    ]
    assert result["strategies"] == ["fixed", "error_aware", "memory_aware", "adaptive"]
    assert len(result["runs"]) == 20
    assert all(Path(item["artifact_path"]).exists() for item in result["runs"])
    for item in result["runs"]:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"


def test_benchmark_scores_are_bounded_and_ranked(tmp_path: Path) -> None:
    result = run_benchmark(tmp_path)
    summaries = {item["strategy"]: item for item in result["summaries"]}
    ranking = result["ranking"]

    assert all(0.0 <= item["total_score"] <= 100.0 for item in summaries.values())
    assert ranking == sorted(
        ranking,
        key=lambda item: (-item["total_score"], item["average_success_steps"], item["strategy"]),
    )
    assert summaries["adaptive"]["total_score"] > summaries["fixed"]["total_score"]
```

- [ ] **Step 2: Verify RED state**

Run: `python -m pytest tests/test_benchmark_suite.py -q`

Expected: collection fails with `ModuleNotFoundError: No module named 'experiments.benchmark_suite'`.

- [ ] **Step 3: Commit tests**

```bash
git add tests/test_benchmark_suite.py
git commit -m "test: define benchmark suite expectations"
```

### Task 2: Implement scenarios, scoring, and ranking

**Files:**
- Create: `experiments/benchmark_suite.py`
- Test: `tests/test_benchmark_suite.py`
- Consumes: `FixedPolicy`, `ErrorAwarePolicy`, `MemoryAwarePolicy`, `AdaptivePolicy`, `RecoveryAwareEvaluator`; existing actions, runner, stopping, metrics, and Artifact APIs.
- Produces: `run_benchmark(output_dir: str | Path = ".loop/runs/benchmark-suite") -> dict[str, object]`.

- [ ] **Step 1: Define stable names and scenario builder**

```python
STRATEGIES = ("fixed", "error_aware", "memory_aware", "adaptive")
SCENARIOS = (
    "steady_progress", "action_failure", "missing_feedback",
    "stalled_progress", "tight_budget",
)

def build_scenario(scenario: str, strategy: str) -> tuple[LoopRunner, LoopState, int]:
    """Return an isolated runner, initial state, and scenario budget."""
```

Use fresh policy/action/evaluator instances. Configure `steady_progress` with `NumericAction`, goal `6.0`, and budget `8`; `action_failure` with the existing `FailOnSecondAction`; `missing_feedback` with a single-failure action and a goal evaluator that omits recovery signals; `stalled_progress` with an action that returns the unchanged value; and `tight_budget` with goal `6.0` and `MaxSteps(3)`. Unknown scenario or strategy raises `ValueError` with the unknown name.

- [ ] **Step 2: Extract one run result and save its Artifact**

```python
def _run_case(root: Path, scenario: str, strategy: str) -> dict[str, object]:
    runner, initial_state, budget = build_scenario(scenario, strategy)
    trace = runner.run(initial_state)
    report = MetricReport.from_trace(trace)
    artifact_path = save_run_artifact(root / f"{scenario}--{strategy}.json", trace, report)
    return {
        "strategy": strategy,
        "scenario": scenario,
        "success": report.success,
        "status": trace.final_state.status if trace.final_state else "RUNNING",
        "steps": report.steps,
        "final_score": report.final_score,
        "failure_count": sum(event.phase == "ACT" and event.payload["success"] is False for event in trace.events),
        "recovery_count": _recovery_count(trace),
        "budget_respected": report.steps <= budget,
        "artifact_path": str(artifact_path),
    }
```

`_recovery_count` counts adaptive `DECIDE` events with `parameters["mode_code"] == 3.0`; for the other strategies it returns `0`.

- [ ] **Step 3: Implement aggregation and exact scores**

```python
def _summarize(strategy: str, runs: list[dict[str, object]]) -> dict[str, object]:
    strategy_runs = [item for item in runs if item["strategy"] == strategy]
    successful = [item for item in strategy_runs if item["success"]]
    success_score = 50.0 * len(successful) / len(SCENARIOS)
    budget_score = 10.0 * sum(item["budget_respected"] for item in strategy_runs) / len(SCENARIOS)
    recovery_runs = [item for item in strategy_runs if item["scenario"] in {"action_failure", "missing_feedback"}]
    recovery_score = 15.0 * sum(item["success"] and item["recovery_count"] >= 1 for item in recovery_runs) / 2
```

Compute efficiency per successful scenario as `25 * best_success_steps_for_that_scenario / strategy_steps`, then average across the 5 scenarios; unsuccessful scenarios contribute `0`. If no strategy succeeds a scenario, its efficiency contribution is `0` for every strategy. Set `total_score` to the sum and `average_success_steps` to the mean successful steps, or `float("inf")` when there are no successes.

- [ ] **Step 4: Implement `run_benchmark` and JSON CLI**

```python
def run_benchmark(output_dir: str | Path = ".loop/runs/benchmark-suite") -> dict[str, object]:
    root = Path(output_dir).resolve()
    runs = [_run_case(root, scenario, strategy) for scenario in SCENARIOS for strategy in STRATEGIES]
    summaries = [_summarize(strategy, runs) for strategy in STRATEGIES]
    ranking = sorted(summaries, key=lambda item: (-float(item["total_score"]), float(item["average_success_steps"]), str(item["strategy"])))
    return {"scenarios": list(SCENARIOS), "strategies": list(STRATEGIES), "runs": runs, "summaries": summaries, "ranking": ranking}
```

Add `main()` that prints `json.dumps(run_benchmark(), ensure_ascii=False, indent=2)`.

- [ ] **Step 5: Verify GREEN state**

Run: `python -m pytest tests/test_benchmark_suite.py -q`

Expected: `2 passed`.

Run: `python experiments/benchmark_suite.py`

Expected: JSON with 20 runs, four summaries, and an ordered ranking where adaptive out-scores fixed.

- [ ] **Step 6: Commit implementation**

```bash
git add experiments/benchmark_suite.py tests/test_benchmark_suite.py
git commit -m "feat: add benchmark suite experiment"
```

### Task 3: Document and fully verify the benchmark

**Files:**
- Create: `docs/benchmark-suite.md`
- Modify: `docs/experiments.md`, `README.md`, `README.zh-CN.md`, `docs/superpowers/sdd/progress.md`

- [ ] **Step 1: Create learner documentation**

Create `docs/benchmark-suite.md` with headings `# Loop Engineering 评测基准`, `## 场景矩阵`, `## 指标与评分`, `## 运行基准`, `## 阅读排行榜`, and `## 解释边界`. Document the 5 scenario names, all 4 score weights, tie rules, Artifact location, and this command:

```powershell
python experiments/benchmark_suite.py
```

- [ ] **Step 2: Update navigation and progress**

Add `python experiments/benchmark_suite.py` after `adaptive_strategy.py` in `docs/experiments.md`, a guide link in both README files, and a progress entry reporting the exact final test count and 20 verified Artifacts.

- [ ] **Step 3: Run full verification**

Run: `python -m pytest -q`

Expected: all tests pass.

Run: `python experiments/benchmark_suite.py`

Expected: 20 run records, four summaries, ranking, and 20 Artifact paths.

Run: `git diff --check`

Expected: exit code `0`.

- [ ] **Step 4: Commit documentation**

```bash
git add docs/benchmark-suite.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain benchmark suite experiment"
```
