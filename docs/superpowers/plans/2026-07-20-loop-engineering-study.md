# Loop Engineering Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `Loop-Engineering-Study` 中建立一个独立的 Loop Engineering 学习与实验项目，用可观测、可复现的运行时解释循环、反馈、记忆、评估、收敛和停止条件。

**Architecture:** 项目以 `Observe → Decide → Act → Evaluate → Feedback` 为核心抽象。第一阶段只实现确定性的本地运行时，不把项目做成生产级 Agent 平台；模型调用作为后续可替换策略，通过事件轨迹、状态快照和指标让每轮循环可检查、可回放、可比较。

**Tech Stack:** Python 3.11+；标准库 `dataclasses`、`enum`、`json`、`argparse`、`pathlib`；pytest 作为开发测试依赖；首版不依赖外部 LLM API、数据库或 Web 框架。

## Global Constraints

- 项目根目录固定为 `E:\IDEWorkplaces\VS\Loop-Engineering-Study`。
- 项目是独立的 Loop Engineering 研究项目，不复刻 `harness-engineering-study` 的领域模型或命令设计。
- 核心循环固定为 `OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK`。
- 每一轮必须产生结构化 trace；不能只返回最终字符串。
- 首版所有实验必须支持 deterministic 模式，保证不调用外部服务也能运行。
- 运行时只使用标准库；pytest 仅放在开发依赖中。
- 状态、事件和指标必须落盘到实验工作目录，且使用 UTF-8 JSON/JSONL。
- 停止条件必须显式可配置，禁止使用无限循环作为默认行为。
- 任何新增策略、动作或评估器都必须有单元测试和至少一个可运行实验。
- 每个阶段结束时运行对应测试，并进行一次独立的小提交。

---

## 目录与文件责任

```text
Loop-Engineering-Study/
├── docs/
│   ├── learning-path.md
│   ├── concepts.md
│   └── experiments.md
├── theory/
│   ├── loop-models.md
│   ├── feedback-systems.md
│   ├── state-and-memory.md
│   ├── convergence.md
│   └── stopping-conditions.md
├── loop_engineering/
│   ├── __init__.py
│   ├── models.py
│   ├── policies.py
│   ├── actions.py
│   ├── evaluators.py
│   ├── stopping.py
│   ├── memory.py
│   ├── metrics.py
│   ├── trace_store.py
│   ├── runner.py
│   └── cli.py
├── experiments/
│   ├── basic_loop.py
│   ├── retry_loop.py
│   └── repair_loop.py
├── examples/
│   └── README.md
├── tests/
│   ├── test_models.py
│   ├── test_runner.py
│   ├── test_stopping.py
│   ├── test_memory.py
│   ├── test_metrics.py
│   └── test_cli.py
├── pyproject.toml
├── README.md
└── README.zh-CN.md
```

`models.py` 只定义领域对象；`runner.py` 只负责推进状态机；策略、动作、评估和停止条件分别通过协议隔离。持久化、指标和 CLI 不得反向污染核心循环逻辑。

## Task 1: 建立独立项目骨架与学习入口

**Files:**
- Create: `pyproject.toml`
- Create: `loop_engineering/__init__.py`
- Create: `.gitignore`
- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `docs/learning-path.md`
- Create: `docs/concepts.md`
- Create: `tests/test_imports.py`

**Interfaces:**
- Produces importable package `loop_engineering` and a documented six-stage learning path.

- [ ] **Step 1: Write the failing import test**

```python
from pathlib import Path


def test_loop_engineering_package_exposes_version():
    import loop_engineering

    assert loop_engineering.__version__ == "0.1.0"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_imports.py -q`

Expected: FAIL because the package and version constant do not exist.

- [ ] **Step 3: Add the minimum package and project metadata**

```python
# loop_engineering/__init__.py
"""可观测、可复现的 Loop Engineering 学习运行时。"""

__version__ = "0.1.0"
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "loop-engineering-study"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`.gitignore` 必须忽略 `.loop/`、`.pytest_cache/`、`__pycache__/` 和 `*.pyc`，保留实验脚本与文档，不提交本地运行产物。

`README.zh-CN.md` 必须说明循环模型、无外部 API 的运行方式、学习顺序和实验目录；`docs/learning-path.md` 按“概念 → 单轮循环 → 反馈 → 记忆 → 收敛 → 工程案例”组织任务；`docs/concepts.md` 只解释首版已经实现的概念。

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_imports.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml loop_engineering/__init__.py .gitignore README.md README.zh-CN.md docs/learning-path.md docs/concepts.md tests/test_imports.py
git commit -m "docs: establish loop engineering study project"
```

## Task 2: 定义循环领域模型与事件轨迹

**Files:**
- Create: `loop_engineering/models.py`
- Create: `loop_engineering/trace_store.py`
- Create: `tests/test_models.py`
- Create: `tests/test_trace_store.py`

**Interfaces:**
- `LoopState`: `step: int`, `value: float`, `goal: float`, `status: str`, `metadata: dict`。
- `LoopEvent`: `step: int`, `phase: str`, `payload: dict`。
- `LoopTrace`: `events: list[LoopEvent]`, `final_state: LoopState | None`，并提供 `append(phase: str, step: int, payload: dict) -> None`。
- `Feedback.empty() -> Feedback` returns a zero-score feedback object with no signals.
- `JsonlTraceStore.append(event: LoopEvent) -> None`。
- `JsonlTraceStore.load() -> list[LoopEvent]`。

- [ ] **Step 1: Write failing model and round-trip tests**

```python
def test_loop_state_is_immutable_by_update():
    from loop_engineering.models import LoopState

    state = LoopState(step=0, value=0.0, goal=3.0)
    updated = state.with_value(1.0)

    assert state.value == 0.0
    assert updated.step == 1
    assert updated.value == 1.0


def test_trace_store_round_trips_jsonl(tmp_path):
    from loop_engineering.models import LoopEvent
    from loop_engineering.trace_store import JsonlTraceStore

    store = JsonlTraceStore(tmp_path / "trace.jsonl")
    event = LoopEvent(step=1, phase="OBSERVE", payload={"value": 2.0})
    store.append(event)

    assert store.load() == [event]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models.py tests/test_trace_store.py -q`

Expected: FAIL because the model and JSONL store are undefined.

- [ ] **Step 3: Implement the domain objects and JSONL persistence**

```python
@dataclass(frozen=True)
class LoopState:
    step: int
    value: float
    goal: float
    status: str = "RUNNING"
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_value(self, value: float, **metadata: Any) -> "LoopState":
        merged = {**self.metadata, **metadata}
        return replace(self, step=self.step + 1, value=value, metadata=merged)
```

`LoopEvent` 必须校验 `phase` 只能是 `OBSERVE`、`DECIDE`、`ACT`、`EVALUATE`、`FEEDBACK`、`STOP`；JSONL 每行写入一个可序列化事件，并在读取时恢复为 `LoopEvent`。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models.py tests/test_trace_store.py -q`

Expected: PASS with zero failures.

- [ ] **Step 5: Commit**

```bash
git add loop_engineering/models.py loop_engineering/trace_store.py tests/test_models.py tests/test_trace_store.py
git commit -m "feat: add loop domain models and traces"
```

## Task 3: 实现可插拔策略、动作与评估器

**Files:**
- Create: `loop_engineering/policies.py`
- Create: `loop_engineering/actions.py`
- Create: `loop_engineering/evaluators.py`
- Create: `tests/test_policies.py`
- Create: `tests/test_actions.py`
- Create: `tests/test_evaluators.py`

**Interfaces:**
- `Policy.decide(state: LoopState, feedback: Feedback) -> Decision`。
- `Action.apply(state: LoopState, decision: Decision) -> ActionResult`。
- `Evaluator.evaluate(before: LoopState, result: ActionResult) -> Evaluation`。
- `Decision`: `name: str` and `parameters: dict[str, float]`。
- `ActionResult`: `state: LoopState`, `success: bool`, and `cost: float`。
- `Feedback`: `score: float`, `message: str`, and `signals: dict[str, float]`。
- `Feedback.empty() -> Feedback` returns `Feedback(score=0.0, message="", signals={})`。
- `Evaluation`: `score: float`, `success: bool`, `message: str`, and `signals: dict[str, float]`。

- [ ] **Step 1: Write the failing deterministic strategy test**

```python
def test_increment_policy_moves_value_toward_goal():
    from loop_engineering.models import Feedback, LoopState
    from loop_engineering.policies import IncrementPolicy

    decision = IncrementPolicy(step_size=1.0).decide(
        LoopState(step=0, value=0.0, goal=3.0), Feedback.empty()
    )

    assert decision.name == "increment"
    assert decision.parameters == {"amount": 1.0}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_policies.py -q`

Expected: FAIL because `IncrementPolicy` does not exist.

- [ ] **Step 3: Implement the minimum adapters**

```python
class IncrementPolicy:
    def __init__(self, step_size: float):
        self.step_size = step_size

    def decide(self, state: LoopState, feedback: Feedback) -> Decision:
        remaining = state.goal - state.value
        amount = min(self.step_size, max(remaining, 0.0))
        return Decision(name="increment", parameters={"amount": amount})
```

`NumericAction` 只处理 `increment` 决策；`GoalEvaluator` 以绝对误差计算分数，并在误差小于等于 `tolerance` 时返回成功。所有未知决策都抛出 `ValueError`，不允许静默执行。

- [ ] **Step 4: Run all adapter tests**

Run: `python -m pytest tests/test_policies.py tests/test_actions.py tests/test_evaluators.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_engineering/policies.py loop_engineering/actions.py loop_engineering/evaluators.py tests/test_policies.py tests/test_actions.py tests/test_evaluators.py
git commit -m "feat: add pluggable loop policy action evaluator"
```

## Task 4: 实现循环运行器与显式停止条件

**Files:**
- Create: `loop_engineering/stopping.py`
- Create: `loop_engineering/runner.py`
- Create: `tests/test_stopping.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- `StopCondition.should_stop(state: LoopState, evaluation: Evaluation, history: Sequence[LoopEvent]) -> StopDecision`。
- `StopDecision`: `stop: bool`, `status: str`, `reason: str`。
- `MaxSteps(max_steps: int)`。
- `SuccessReached()`。
- `LoopRunner.run(initial_state: LoopState) -> LoopTrace`。

- [ ] **Step 1: Write failing tests for success, maximum steps and trace order**

```python
from loop_engineering.models import LoopState


def build_numeric_runner(max_steps: int):
    from loop_engineering.actions import NumericAction
    from loop_engineering.evaluators import GoalEvaluator
    from loop_engineering.policies import IncrementPolicy
    from loop_engineering.runner import LoopRunner
    from loop_engineering.stopping import MaxSteps, SuccessReached

    return LoopRunner(
        policy=IncrementPolicy(step_size=1.0),
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(max_steps)],
    )


def test_runner_stops_when_goal_is_reached():
    trace = build_numeric_runner(max_steps=10).run(
        LoopState(step=0, value=0.0, goal=2.0)
    )

    assert trace.final_state.status == "SUCCEEDED"
    assert trace.final_state.value == 2.0
    assert trace.events[-1].phase == "STOP"


def test_runner_stops_at_maximum_steps():
    trace = build_numeric_runner(max_steps=1).run(
        LoopState(step=0, value=0.0, goal=5.0)
    )

    assert trace.final_state.status == "STOPPED"
    assert trace.final_state.step == 1
    assert [event.phase for event in trace.events] == [
        "OBSERVE", "DECIDE", "ACT", "EVALUATE", "FEEDBACK", "STOP"
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_stopping.py tests/test_runner.py -q`

Expected: FAIL because the runner and stop conditions do not exist.

- [ ] **Step 3: Implement the phase machine**

`LoopRunner` 必须在每轮严格按以下顺序写事件：

```python
for phase in ("OBSERVE", "DECIDE", "ACT", "EVALUATE", "FEEDBACK"):
    trace.append(phase, step, payload)
```

运行器在每轮结束后依次检查 `SuccessReached` 和 `MaxSteps`，命中后写入 `STOP` 事件并返回；如果所有停止条件都未命中且达到安全上限，则返回 `STOPPED`，不能进入无限循环。反馈对象由上一轮 `Evaluation` 生成，并传入下一轮策略。

- [ ] **Step 4: Run the full runtime tests**

Run: `python -m pytest tests/test_stopping.py tests/test_runner.py -q`

Expected: PASS; trace phase order must be asserted explicitly.

- [ ] **Step 5: Commit**

```bash
git add loop_engineering/stopping.py loop_engineering/runner.py tests/test_stopping.py tests/test_runner.py
git commit -m "feat: implement observable loop runner"
```

## Task 5: 加入记忆、指标和实验持久化

**Files:**
- Create: `loop_engineering/memory.py`
- Create: `loop_engineering/metrics.py`
- Create: `tests/test_memory.py`
- Create: `tests/test_metrics.py`
- Modify: `loop_engineering/runner.py`
- Modify: `loop_engineering/models.py`

**Interfaces:**
- `WorkingMemory.add(event: LoopEvent) -> None`。
- `WorkingMemory.recent(limit: int) -> list[LoopEvent]`。
- `MetricReport.from_trace(trace: LoopTrace) -> MetricReport`。
- `MetricReport`: `steps`, `final_score`, `success`, `cost`, `average_step_gain`。

- [ ] **Step 1: Write failing memory and metric tests**

```python
from loop_engineering.models import LoopEvent, LoopState, LoopTrace


def event(step: int, score: float = 0.0) -> LoopEvent:
    return LoopEvent(
        step=step,
        phase="EVALUATE",
        payload={"score": score},
    )


def test_working_memory_keeps_only_recent_events():
    memory = WorkingMemory(capacity=2)
    memory.add(event(1))
    memory.add(event(2))
    memory.add(event(3))

    assert [item.step for item in memory.recent(10)] == [2, 3]


def trace_with_scores(scores: list[float]) -> LoopTrace:
    events = [event(step, score) for step, score in enumerate(scores)]
    return LoopTrace(events=events, final_state=LoopState(
        step=max(len(scores) - 1, 0), value=scores[-1], goal=1.0,
        status="SUCCEEDED",
    ))


def test_metric_report_counts_steps_and_gain():
    report = MetricReport.from_trace(trace_with_scores([0.0, 0.5, 1.0]))

    assert report.steps == 2
    assert report.final_score == 1.0
    assert report.average_step_gain == 0.5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_memory.py tests/test_metrics.py -q`

Expected: FAIL because memory and metrics are undefined.

- [ ] **Step 3: Implement bounded memory and trace-derived metrics**

`WorkingMemory` 使用 `collections.deque(maxlen=capacity)`，不允许无限积累；`MetricReport.from_trace` 只从 trace 计算结果，不修改运行状态。`LoopRunner` 在每轮将事件写入 `WorkingMemory`，并把 memory 的最近事件提供给策略。

- [ ] **Step 4: Run tests and a deterministic smoke experiment**

Run: `python -m pytest tests/test_memory.py tests/test_metrics.py tests/test_runner.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add loop_engineering/memory.py loop_engineering/metrics.py loop_engineering/models.py loop_engineering/runner.py tests/test_memory.py tests/test_metrics.py
git commit -m "feat: add loop memory and metrics"
```

## Task 6: 提供命令行入口和可回放输出

**Files:**
- Create: `loop_engineering/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_cli.py`
- Modify: `README.zh-CN.md`

**Interfaces:**
- `python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json`。
- CLI 输出 JSON 摘要：`status`、`steps`、`final_value`、`score`、`trace_path`。

- [ ] **Step 1: Write the failing CLI test**

```python
def test_cli_run_writes_replayable_trace(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "loop_engineering.cli", "run",
         "--goal", "2", "--max-steps", "5", "--output",
         str(tmp_path / "run.json")],
        check=False, capture_output=True, text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "SUCCEEDED"
    assert Path(payload["trace_path"]).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -q`

Expected: FAIL because the module command is not implemented.

- [ ] **Step 3: Implement the CLI with the standard library**

```python
parser = argparse.ArgumentParser(prog="loop-engineering")
subparsers = parser.add_subparsers(dest="command", required=True)
run = subparsers.add_parser("run")
run.add_argument("--goal", type=float, required=True)
run.add_argument("--max-steps", type=int, default=20)
run.add_argument("--output", type=Path, required=True)
```

`run` 命令使用 Task 4 的确定性数值循环，写入 JSON trace 和 JSON 摘要；`--max-steps` 小于 1 时返回非零退出码并输出明确错误。README 必须包含一条可复制的 Windows PowerShell 和一条 POSIX 命令。

- [ ] **Step 4: Run CLI and package tests**

Run: `python -m pytest tests/test_cli.py tests/test_runner.py -q`

Expected: PASS; subprocess exit code is zero for a successful run.

- [ ] **Step 5: Commit**

```bash
git add loop_engineering/cli.py pyproject.toml tests/test_cli.py README.zh-CN.md
git commit -m "feat: add loop experiment command line"
```

## Task 7: 建立三个可重复实验与理论文档

**Files:**
- Create: `experiments/basic_loop.py`
- Create: `experiments/retry_loop.py`
- Create: `experiments/repair_loop.py`
- Create: `theory/loop-models.md`
- Create: `theory/feedback-systems.md`
- Create: `theory/state-and-memory.md`
- Create: `theory/convergence.md`
- Create: `theory/stopping-conditions.md`
- Create: `docs/experiments.md`
- Create: `examples/README.md`
- Create: `tests/test_experiments.py`

**Interfaces:**
- 每个实验都暴露 `run() -> LoopTrace`。
- 每个实验都能通过 `python experiments/<name>.py` 运行，并打印指标摘要。

- [ ] **Step 1: Write failing experiment contract tests**

```python
@pytest.mark.parametrize("module_name", ["basic_loop", "retry_loop", "repair_loop"])
def test_experiment_returns_trace(module_name):
    module = importlib.import_module(f"experiments.{module_name}")

    trace = module.run()

    assert trace.final_state is not None
    assert trace.events
    assert trace.events[-1].phase == "STOP"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_experiments.py -q`

Expected: FAIL because the experiment modules do not exist.

- [ ] **Step 3: Implement the experiments**

实验必须展示不同的 Loop Engineering 问题：

1. `basic_loop.py`：展示稳定的目标逼近循环。
2. `retry_loop.py`：注入一次确定性失败，展示反馈如何改变下一轮动作。
3. `repair_loop.py`：模拟错误评估结果，展示“动作成功”与“目标达成”不是同一件事。

每个实验输出至少包含：总轮数、最终状态、最终分数、停止原因和每轮得分序列。理论文档必须分别解释模型、反馈、状态/记忆、收敛和停止条件，并链接到对应实验。

- [ ] **Step 4: Run experiment and documentation checks**

Run: `python -m pytest tests/test_experiments.py -q`

Expected: PASS.

Run: `python experiments/basic_loop.py`

Expected: 输出包含 `status=SUCCEEDED`、`steps=` 和 `score=`。

- [ ] **Step 5: Commit**

```bash
git add experiments theory docs/experiments.md examples/README.md tests/test_experiments.py
git commit -m "docs: add loop engineering experiments and theory"
```

## Task 8: 完成项目级验证与学习体验检查

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/learning-path.md`
- Create: `tests/test_project_contract.py`

**Interfaces:**
- 新用户能够在没有 API Key 的情况下完成安装、运行第一个循环、查看 trace、阅读实验说明。

- [ ] **Step 1: Write project contract tests**

```python
def test_learning_path_links_to_existing_files():
    text = Path("docs/learning-path.md").read_text(encoding="utf-8")

    for relative_path in [
        "theory/loop-models.md",
        "theory/feedback-systems.md",
        "experiments/basic_loop.py",
    ]:
        assert relative_path in text
        assert Path(relative_path).exists()
```

- [ ] **Step 2: Run the complete verification suite**

Run: `python -m pytest -q`

Expected: all tests pass with zero failures.

Run: `python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/final.json`

Expected: exit code 0; JSON output reports `SUCCEEDED`; `.loop/runs/final.json` contains `OBSERVE`, `DECIDE`, `ACT`, `EVALUATE`, `FEEDBACK` and `STOP` events.

- [ ] **Step 3: Perform manual documentation review**

检查 README 是否明确回答：

- Loop Engineering 研究什么；
- 一轮循环有哪些阶段；
- 如何运行第一个实验；
- 如何查看 trace 和指标；
- 为什么首版不接入外部模型；
- 下一阶段如何扩展策略、记忆和评估器。

- [ ] **Step 4: Scan for plan and documentation gaps**

Run: `rg -n "TODO|TBD|待补充|占位" README.md README.zh-CN.md docs theory experiments loop_engineering tests`

Expected: no output.

- [ ] **Step 5: Commit the verified project baseline**

```bash
git add README.md README.zh-CN.md .gitignore docs theory experiments loop_engineering tests pyproject.toml
git commit -m "chore: verify loop engineering study baseline"
```

## 验收标准

完成本计划后，项目必须满足：

1. 用户可以不配置任何外部 API，运行一个完整的确定性循环。
2. 每轮都能看到五个核心阶段的结构化事件。
3. 循环可以因成功、最大步数或其他显式条件停止。
4. trace、最终状态和指标可以落盘并重新读取。
5. 策略、动作、评估器、记忆和停止条件可以独立替换和测试。
6. 至少三个实验展示不同的 Loop Engineering 问题。
7. 理论文档与实验代码相互链接，而不是只提供抽象描述。
8. `python -m pytest -q` 通过，CLI smoke test 通过。

## 执行交接

计划完成并保存到 `docs/superpowers/plans/2026-07-20-loop-engineering-study.md`。两种执行方式：

1. **Subagent-Driven（推荐）**：每个 Task 使用新的子代理执行，并在任务之间进行两阶段审查。
2. **Inline Execution**：在当前会话中使用 `superpowers:executing-plans` 分批执行，并设置检查点。
