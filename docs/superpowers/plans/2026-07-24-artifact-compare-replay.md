# Artifact 对比与回放工具 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过现有 CLI 为任意兼容的 Loop Artifact 提供完整回放与确定性首分歧对比。

**Architecture:** `loop_engineering.cli` 新增 `replay` 与 `compare` 子命令，分别编排既有 `load_run_artifact()` 和纯函数 `compare_traces()`。CLI 使用 `dataclasses.asdict()` 将领域对象和比较结果转为 JSON；Artifact 读取、校验与 Trace 比较规则保持在已有模块中。

**Tech Stack:** Python 3.11、标准库 argparse/json/dataclasses、pytest。

## Global Constraints

- 保持 `save_run_artifact()` 写入格式、`load_run_artifact()` 错误语义与既有 `run` 命令输出契约不变。
- `replay` 必须输出全部有序事件、最终状态、指标和绝对 Artifact 路径。
- `compare` 必须复用 `loop_engineering.trace_diff.compare_traces()`，不可实现第二套差异规则。
- 成功路径只向标准输出打印 UTF-8 JSON；参数或 Artifact 读取错误继续通过 argparse/既有加载器暴露。
- 每项实现先写失败测试，再写最小实现；每个任务结束时运行指定验证并提交。

---

## File structure

- `loop_engineering/cli.py`：解析三种子命令，运行既有循环或编排 Artifact 回放/比较，并序列化 JSON 输出。
- `tests/test_cli.py`：通过真实子进程验证 CLI 的 `run`、`replay` 与 `compare` 契约。
- `docs/replay.md`：描述通用回放、对比命令和只读边界。
- `docs/experiments.md`、`README.md`、`README.zh-CN.md`、`docs/superpowers/sdd/progress.md`：接入导航与进度记录。

## Task 1: Add replay command with full Artifact output

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `loop_engineering/cli.py`

**Interfaces:**
- Consumes: `load_run_artifact(path: str | Path) -> tuple[LoopTrace, MetricReport]`。
- Produces: `replay_artifact(path: Path) -> dict[str, object]` and CLI command `replay <artifact-path>`.

- [ ] **Step 1: Write the failing replay integration test**

Add imports and this test to `tests/test_cli.py`:

```python
from loop_engineering.cli import run_loop, write_trace


def test_cli_replay_prints_complete_saved_artifact(tmp_path: Path) -> None:
    artifact_path = write_trace(tmp_path / "run.json", run_loop(2.0, 5))

    result = run_cli("replay", str(artifact_path))

    assert result.returncode == 0, result.stderr
    replayed = json.loads(result.stdout)
    persisted = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert replayed == {
        "artifact_path": str(artifact_path.resolve()),
        "events": persisted["events"],
        "final_state": persisted["final_state"],
        "metrics": persisted["metrics"],
    }
```

- [ ] **Step 2: Run test to verify RED**

Run: `python -m pytest tests/test_cli.py::test_cli_replay_prints_complete_saved_artifact -q`

Expected: failure because `replay` is not an accepted CLI command.

- [ ] **Step 3: Write minimal replay implementation**

In `loop_engineering/cli.py`, import `asdict` and `load_run_artifact`. Add this parser setup after the existing `run` arguments:

```python
    replay_parser = subparsers.add_parser("replay", help="print a complete saved artifact")
    replay_parser.add_argument("artifact", type=Path)
```

Add the helper before `main()`:

```python
def replay_artifact(path: Path) -> dict[str, object]:
    """Load one Artifact and return its complete JSON-ready run boundary."""

    trace, metrics = load_run_artifact(path)
    return {
        "artifact_path": str(path.resolve()),
        "events": [asdict(event) for event in trace.events],
        "final_state": asdict(trace.final_state) if trace.final_state is not None else None,
        "metrics": asdict(metrics),
    }
```

At the start of `main()`, after parsing arguments and before run-only validation, dispatch:

```python
    if args.command == "replay":
        json.dump(replay_artifact(args.artifact), fp=sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 4: Run test to verify GREEN**

Run: `python -m pytest tests/test_cli.py::test_cli_replay_prints_complete_saved_artifact -q`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add loop_engineering/cli.py tests/test_cli.py
git commit -m "feat: add artifact replay command"
```

## Task 2: Add compare command using the existing Trace comparator

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `loop_engineering/cli.py`

**Interfaces:**
- Consumes: `load_run_artifact()` and `compare_traces(left_trace, right_trace, left_metrics, right_metrics) -> TraceComparison`.
- Produces: `compare_artifacts(left: Path, right: Path) -> dict[str, object]` and CLI command `compare <left-artifact> <right-artifact>`.

- [ ] **Step 1: Write failing identical and differing comparison tests**

Append to `tests/test_cli.py`:

```python
def test_cli_compare_reports_identical_for_same_artifact(tmp_path: Path) -> None:
    artifact_path = write_trace(tmp_path / "same.json", run_loop(2.0, 5))

    result = run_cli("compare", str(artifact_path), str(artifact_path))

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "left_artifact_path": str(artifact_path.resolve()),
        "right_artifact_path": str(artifact_path.resolve()),
        "identical": True,
        "difference": None,
    }


def test_cli_compare_reports_first_difference_between_artifacts(tmp_path: Path) -> None:
    left_path = write_trace(tmp_path / "left.json", run_loop(2.0, 5))
    right_path = write_trace(tmp_path / "right.json", run_loop(3.0, 5))

    result = run_cli("compare", str(left_path), str(right_path))

    assert result.returncode == 0, result.stderr
    comparison = json.loads(result.stdout)
    assert comparison["left_artifact_path"] == str(left_path.resolve())
    assert comparison["right_artifact_path"] == str(right_path.resolve())
    assert comparison["identical"] is False
    assert comparison["difference"] == {
        "scope": "event",
        "event_index": 0,
        "step": 0,
        "phase": "OBSERVE",
        "field_path": ["payload", "goal"],
        "baseline_value": 2.0,
        "repaired_value": 3.0,
    }
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_cli.py -k compare -q`

Expected: failures because `compare` is not an accepted CLI command.

- [ ] **Step 3: Write minimal compare implementation**

In `loop_engineering/cli.py`, import `compare_traces` and add parser setup:

```python
    compare_parser = subparsers.add_parser("compare", help="compare two saved artifacts")
    compare_parser.add_argument("left_artifact", type=Path)
    compare_parser.add_argument("right_artifact", type=Path)
```

Add the helper before `main()`:

```python
def compare_artifacts(left_path: Path, right_path: Path) -> dict[str, object]:
    """Return the existing first-difference comparison for two Artifacts."""

    left_trace, left_metrics = load_run_artifact(left_path)
    right_trace, right_metrics = load_run_artifact(right_path)
    comparison = compare_traces(left_trace, right_trace, left_metrics, right_metrics)
    return {
        "left_artifact_path": str(left_path.resolve()),
        "right_artifact_path": str(right_path.resolve()),
        "identical": comparison.identical,
        "difference": (
            asdict(comparison.first_difference)
            if comparison.first_difference is not None
            else None
        ),
    }
```

Add this dispatch after the replay branch:

```python
    if args.command == "compare":
        json.dump(
            compare_artifacts(args.left_artifact, args.right_artifact),
            fp=sys.stdout,
            ensure_ascii=False,
        )
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 4: Run comparison and CLI regression tests to verify GREEN**

Run: `python -m pytest tests/test_cli.py -q`

Expected: all CLI tests pass, including existing `run` success and invalid-step tests.

- [ ] **Step 5: Commit**

```powershell
git add loop_engineering/cli.py tests/test_cli.py
git commit -m "feat: add artifact compare command"
```

## Task 3: Document generic Artifact tooling and verify the project

**Files:**
- Modify: `docs/replay.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: implemented `python -m loop_engineering.cli replay <artifact-path>` and `python -m loop_engineering.cli compare <left-artifact> <right-artifact>`.
- Produces: discoverable usage documentation that distinguishes generic CLI tooling from `experiments/trace_diff_analysis.py`.

- [ ] **Step 1: Update replay documentation**

In `docs/replay.md`, add this section after the loading example:

```markdown
## Replay and compare from the CLI

```powershell
python -m loop_engineering.cli replay .loop/runs/demo.json
python -m loop_engineering.cli compare .loop/runs/baseline.json .loop/runs/repaired.json
```

`replay` prints the complete ordered events, final state, and metrics from one
Artifact. `compare` prints whether two Artifacts are identical and, when they
are not, the first observable event, final-state, or metric difference. Both
commands are read-only: they load evidence and never execute stored actions.
```

Replace the experiment-only comparison paragraph with language identifying `trace_diff_analysis.py` as a scenario-specific report using the same first-difference semantics.

- [ ] **Step 2: Update navigation and progress**

1. In `docs/experiments.md`, replace the opening Trace-pair-only sentence with links to generic `replay.md` tooling and the scenario-specific Trace-diff guide.
2. In `README.md`, insert `[Artifact replay and comparison](docs/replay.md)` immediately after `[Trace difference analysis](docs/trace-diff-analysis.md)`, then renumber subsequent entries.
3. In `README.zh-CN.md`, add a top-level `[Artifact 回放与对比](docs/replay.md)` line immediately below the title, explaining that it reads one Artifact or compares any two without rerunning actions.
4. Append a Phase 2 progress entry stating the two generic commands, full Artifact output, reused first-difference comparison, and the final pytest count.

- [ ] **Step 3: Run end-to-end commands and complete suite**

Run:

```powershell
python -m loop_engineering.cli run --goal 2 --max-steps 5 --output .loop/runs/artifact-tools-demo.json
python -m loop_engineering.cli replay .loop/runs/artifact-tools-demo.json
python -m loop_engineering.cli compare .loop/runs/artifact-tools-demo.json .loop/runs/artifact-tools-demo.json
python -m pytest -q
git diff --check
```

Expected: the first command creates an Artifact, replay emits complete JSON, self-comparison emits `"identical": true`, all tests pass, and the whitespace check has no output.

- [ ] **Step 4: Commit documentation**

```powershell
git add docs/replay.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: document artifact tooling"
```

