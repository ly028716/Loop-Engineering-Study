# Trace 差异分析实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (\`- [ ]\`) syntax for tracking.

**Goal:** 为成对的 Loop Trace 定位首个顺序分歧，并对三组诊断修复案例生成可持久化的差异分析报告。

**Architecture:** \`loop_engineering.trace_diff\` 是不访问文件系统的纯比较模块，按事件索引比较事件、递归比较 payload，再比较最终状态和指标。 \`experiments.trace_diff_analysis\` 复用既有诊断修复实验生成的 Artifact，对每对 Artifact 进行比较并写出稳定 JSON 报告。

**Tech Stack:** Python 3.11、标准库 \`dataclasses\`/ \`json\`、pytest。

## Global Constraints

- 不添加依赖，不修改 \`LoopRunner\`、\`diagnose_trace\` 或 Artifact JSON 格式。
- 比较采用事件索引顺序对齐，不实现编辑距离、动态规划或重放。
- 第一处差异一经确定即停止事件/字段定位；最终状态和指标仍作为运行摘要保留。
- 必须支持空事件 Trace、\`None\` 最终状态、失败运行和不同长度的 Trace。
- 实验仅处理 \`action_failure\`、\`stalled_progress\`、\`tight_budget\`，并保持该顺序。
- 报告写入 \`.loop/runs/trace-diff-analysis/report.json\`，使用 UTF-8、\`ensure_ascii=False\`、缩进 JSON 和末尾换行。

---

## File Structure

- Create \`loop_engineering/trace_diff.py\`: 比较数据模型、递归字段比较和公共 \`compare_traces\` 入口。
- Create \`tests/test_trace_diff.py\`: 纯比较模块的首分歧与边界行为测试。
- Create \`experiments/trace_diff_analysis.py\`: 诊断修复 Artifact 的成对比较、报告持久化和 JSON CLI。
- Create \`tests/test_trace_diff_analysis.py\`: 三案例实验、报告结构和顺序稳定性测试。
- Create \`docs/trace-diff-analysis.md\`: 学习者指南，说明首分歧的解释边界和运行方式。
- Modify \`docs/experiments.md\`, \`README.md\`, \`README.zh-CN.md\`, \`docs/replay.md\`, \`docs/superpowers/sdd/progress.md\`: 接入实验导航、回放能力说明和项目进度。

### Task 1: 建立 Trace 首分歧比较模块

**Files:**

- Create: \`tests/test_trace_diff.py\`
- Create: \`loop_engineering/trace_diff.py\`

**Interfaces:**

- Consumes: \`loop_engineering.models.LoopEvent\`, \`LoopState\`, \`LoopTrace\`；\`loop_engineering.metrics.MetricReport\`。
- Produces: \`TraceDifference\`、\`TraceComparison\` 和 \`compare_traces(baseline: LoopTrace, repaired: LoopTrace, baseline_metrics: MetricReport, repaired_metrics: MetricReport) -> TraceComparison\`。

- [ ] **Step 1: 写入失败测试，固定公共接口和事件差异语义**

\`\`\`python
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.trace_diff import compare_traces


def _metrics(*, score: float = 1.0) -> MetricReport:
    return MetricReport(
        steps=1, final_score=score, success=True, cost=1.0, average_step_gain=0.0
    )


def test_compare_traces_returns_identical_for_matching_boundaries() -> None:
    trace = LoopTrace(
        final_state=LoopState(step=1, value=1.0, goal=1.0, status="SUCCEEDED")
    )

    result = compare_traces(trace, trace, _metrics(), _metrics())

    assert result.identical is True
    assert result.first_difference is None
    assert result.baseline_event_count == result.repaired_event_count == 0


def test_compare_traces_reports_first_payload_field_difference() -> None:
    baseline = LoopTrace()
    baseline.append("DECIDE", 0, {"name": "increment", "parameters": {"size": 1.0}})
    repaired = LoopTrace()
    repaired.append("DECIDE", 0, {"name": "increment", "parameters": {"size": 2.0}})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.identical is False
    assert result.first_difference is not None
    assert result.first_difference.scope == "event"
    assert result.first_difference.event_index == 0
    assert result.first_difference.field_path == ("payload", "parameters", "size")
    assert result.first_difference.baseline_value == 1.0
    assert result.first_difference.repaired_value == 2.0
\`\`\`

- [ ] **Step 2: 运行测试确认 RED 状态**

Run: \`python -m pytest tests/test_trace_diff.py -q\`

Expected: collection fails with \`ModuleNotFoundError: No module named 'loop_engineering.trace_diff'\`。

- [ ] **Step 3: 实现数据模型和最小比较器**

\`\`\`python
@dataclass(frozen=True)
class TraceDifference:
    scope: str
    event_index: int | None
    step: int | None
    phase: str | None
    field_path: tuple[str | int, ...]
    baseline_value: object
    repaired_value: object


@dataclass(frozen=True)
class TraceComparison:
    identical: bool
    first_difference: TraceDifference | None
    baseline_event_count: int
    repaired_event_count: int
    baseline_final_state: dict[str, object] | None
    repaired_final_state: dict[str, object] | None
    baseline_metrics: dict[str, object]
    repaired_metrics: dict[str, object]
\`\`\`

实现 \`_first_value_difference(baseline, repaired, path=())\`：当两个值相等时返回 \`None\`；两个字典按 \`sorted(set(baseline) | set(repaired))\` 检查键；列表先比较长度，再按索引递归；其他值返回当前 \`path\`。使用一个私有 sentinel 区分“键不存在”与值为 \`None\`。

实现 \`compare_traces\`：先枚举共同长度的事件并依次比较 \`step\`、\`phase\`、\`payload\`；再处理事件数量差异；若所有事件一致，依次比较 \`final_state\` 与指标。所有 \`LoopState\` 和 \`MetricReport\` 快照通过 \`dataclasses.asdict\` 转成可 JSON 序列化的字典。首分歧的 \`scope\` 分别使用 \`event\`、\`event_count\`、\`final_state\`、\`metrics\`。

- [ ] **Step 4: 运行基础测试确认 GREEN 状态**

Run: \`python -m pytest tests/test_trace_diff.py -q\`

Expected: \`2 passed\`。

- [ ] **Step 5: 提交核心比较能力**

\`\`\`bash
git add loop_engineering/trace_diff.py tests/test_trace_diff.py
git commit -m "feat: add trace first-difference comparison"
\`\`\`

### Task 2: 覆盖比较边界与运行摘要

**Files:**

- Modify: \`tests/test_trace_diff.py\`
- Modify: \`loop_engineering/trace_diff.py\`

**Interfaces:**

- Consumes: Task 1 的 \`compare_traces\` 和只读结果数据模型。
- Produces: 对 \`step\`、\`phase\`、事件长度、最终状态和指标差异的稳定契约。

- [ ] **Step 1: 增加失败测试，覆盖剩余首分歧类型**

\`\`\`python
def test_compare_traces_stops_at_step_difference_before_payload() -> None:
    baseline = LoopTrace()
    baseline.append("OBSERVE", 0, {"value": 0.0})
    repaired = LoopTrace()
    repaired.append("OBSERVE", 1, {"value": 9.0})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.field_path == ("step",)
    assert result.first_difference.baseline_value == 0
    assert result.first_difference.repaired_value == 1


def test_compare_traces_reports_phase_difference_before_payload() -> None:
    baseline = LoopTrace()
    baseline.append("OBSERVE", 0, {"value": 0.0})
    repaired = LoopTrace()
    repaired.append("DECIDE", 0, {"value": 9.0})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.field_path == ("phase",)
    assert result.first_difference.baseline_value == "OBSERVE"
    assert result.first_difference.repaired_value == "DECIDE"


def test_compare_traces_reports_added_event_after_matching_prefix() -> None:
    baseline = LoopTrace()
    repaired = LoopTrace()
    repaired.append("STOP", 0, {"status": "FAILED"})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.scope == "event_count"
    assert result.first_difference.event_index == 0
    assert result.first_difference.baseline_value is None
    assert result.first_difference.repaired_value == {
        "step": 0, "phase": "STOP", "payload": {"status": "FAILED"}
    }


def test_compare_traces_reports_final_state_then_metric_difference() -> None:
    baseline = LoopTrace(
        final_state=LoopState(step=1, value=1.0, goal=1.0, status="SUCCEEDED")
    )
    repaired = LoopTrace(
        final_state=LoopState(step=1, value=0.0, goal=1.0, status="FAILED")
    )

    state_result = compare_traces(baseline, repaired, _metrics(), _metrics())
    metric_result = compare_traces(baseline, baseline, _metrics(), _metrics(score=0.5))

    assert state_result.first_difference is not None
    assert state_result.first_difference.scope == "final_state"
    assert metric_result.first_difference is not None
    assert metric_result.first_difference.scope == "metrics"
    assert metric_result.baseline_metrics["final_score"] == 1.0
    assert metric_result.repaired_metrics["final_score"] == 0.5
\`\`\`

- [ ] **Step 2: 运行新增测试确认 RED 状态**

Run: \`python -m pytest tests/test_trace_diff.py -q\`

Expected: 至少 1 个新增断言失败，因为 Task 1 尚未处理所有边界。

- [ ] **Step 3: 补齐事件结构、运行边界和指标差异实现**

为 \`step\`、\`phase\` 和 \`payload\` 生成明确字段路径。事件长度不一致时，将缺失侧记录为 \`None\`，存在侧记录为 \`asdict(event)\`，并把第一个超出公共前缀的索引写入 \`event_index\`。当事件相同后，分别将 \`asdict(final_state)\` 与 \`asdict(metrics)\` 输入递归比较器；为它们构造 \`event_index=None\`、\`step=None\`、\`phase=None\` 的 \`TraceDifference\`。

- [ ] **Step 4: 验证完整纯比较模块**

Run: \`python -m pytest tests/test_trace_diff.py -q\`

Expected: \`6 passed\`。

Run: \`python -m pytest -q\`

Expected: 现有全套测试与新增测试全部通过。

- [ ] **Step 5: 提交边界行为**

\`\`\`bash
git add loop_engineering/trace_diff.py tests/test_trace_diff.py
git commit -m "test: cover trace comparison boundaries"
\`\`\`

### Task 3: 构建诊断修复 Trace 差异实验

**Files:**

- Create: \`tests/test_trace_diff_analysis.py\`
- Create: \`experiments/trace_diff_analysis.py\`

**Interfaces:**

- Consumes: \`experiments.diagnosis_repair_loop.run_repair_loop\`，\`loop_engineering.artifacts.load_run_artifact\`，Task 1 的 \`compare_traces\`，\`dataclasses.asdict\`。
- Produces: \`run_trace_diff_analysis(output_dir: str | Path = ".loop/runs/trace-diff-analysis") -> list[dict[str, object]]\`。

- [ ] **Step 1: 写入失败的实验报告测试**

\`\`\`python
import json
from pathlib import Path

from experiments.trace_diff_analysis import run_trace_diff_analysis


def test_trace_diff_analysis_compares_each_repair_case(tmp_path: Path) -> None:
    results = run_trace_diff_analysis(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure",
        "stalled_progress",
        "tight_budget",
    ]
    assert all(item["repair_succeeded"] is True for item in results)
    assert all(item["comparison"]["first_difference"] is not None for item in results)
    assert all(item["comparison"]["identical"] is False for item in results)
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report == results


def test_trace_diff_analysis_keeps_case_order_stable(tmp_path: Path) -> None:
    first = run_trace_diff_analysis(tmp_path / "first")
    second = run_trace_diff_analysis(tmp_path / "second")

    assert [item["case"] for item in first] == [item["case"] for item in second]
    assert [item["comparison"]["first_difference"] for item in first] == [
        item["comparison"]["first_difference"] for item in second
    ]
\`\`\`

- [ ] **Step 2: 运行测试确认 RED 状态**

Run: \`python -m pytest tests/test_trace_diff_analysis.py -q\`

Expected: collection fails with \`ModuleNotFoundError: No module named 'experiments.trace_diff_analysis'\`。

- [ ] **Step 3: 实现成对 Artifact 比较与 CLI**

\`run_trace_diff_analysis\` 必须将给定输出目录解析为绝对路径，在其 \`repair-loop/\` 子目录调用 \`run_repair_loop\`，并按其返回的既有顺序处理案例。对每个记录加载 \`baseline_artifact_path\` 和 \`repaired_artifact_path\`，传入 \`compare_traces\`，并创建下列结果：

\`\`\`python
{
    "case": repair_result["case"],
    "baseline_artifact_path": repair_result["baseline_artifact_path"],
    "repaired_artifact_path": repair_result["repaired_artifact_path"],
    "repair_succeeded": repair_result["repair_succeeded"],
    "comparison": asdict(comparison),
}
\`\`\`

使用 \`_save_report(root / "report.json", results)\` 持久化整个列表；该辅助函数以 \`json.dumps(payload, ensure_ascii=False, indent=2) + "\\n"\` 写入 UTF-8。采用与 \`experiments.trace_diagnostics\` 相同的 \`_bootstrap.py\` 直跑导入约定。 \`main()\` 打印 \`json.dumps(run_trace_diff_analysis(), ensure_ascii=False, indent=2)\`。

- [ ] **Step 4: 验证实验报告与 CLI**

Run: \`python -m pytest tests/test_trace_diff_analysis.py -q\`

Expected: \`2 passed\`。

Run: \`python experiments/trace_diff_analysis.py\`

Expected: 输出 3 个按案例顺序排列的 JSON 记录；每个记录均有非空的 \`comparison.first_difference\`，并在 \`.loop/runs/trace-diff-analysis/report.json\` 生成同内容报告。

- [ ] **Step 5: 提交实验集成**

\`\`\`bash
git add experiments/trace_diff_analysis.py tests/test_trace_diff_analysis.py
git commit -m "feat: add trace diff analysis experiment"
\`\`\`

### Task 4: 说明学习用法并完成集成验证

**Files:**

- Create: \`docs/trace-diff-analysis.md\`
- Modify: \`docs/experiments.md\`
- Modify: \`README.md\`
- Modify: \`README.zh-CN.md\`
- Modify: \`docs/replay.md\`
- Modify: \`docs/superpowers/sdd/progress.md\`

**Interfaces:**

- Consumes: \`python experiments/trace_diff_analysis.py\` 和 Task 3 的 \`.loop/runs/trace-diff-analysis/report.json\`。
- Produces: 可导航的学习说明与最新项目进度记录。

- [ ] **Step 1: 编写学习者文档**

创建 \`docs/trace-diff-analysis.md\`，包含 \`# Trace 差异分析\`、\`## 运行实验\`、\`## 如何阅读首分歧\`、\`## 报告结构\`、\`## 解释边界\` 标题，并包含：

\`\`\`powershell
python experiments/trace_diff_analysis.py
\`\`\`

说明报告比较的是同一案例的基线与修复后 Artifact；\`event\`、\`event_count\`、\`final_state\`、\`metrics\` 四个 \`scope\` 的含义；首分歧是后续行为变化的起点而非自动根因判断；运行不会重放或修改既有 Artifact。

- [ ] **Step 2: 更新导航、回放说明与进度**

在 \`docs/experiments.md\` 的诊断修复实验之后加入上述命令与文档链接。在两份 README 学习路径中，将 Trace 差异分析放在诊断修复闭环之后。在 \`docs/replay.md\` 中将“未来可做 step-by-step comparison”更新为“当前已有只读首分歧比较”，并链接到新文档。在 \`docs/superpowers/sdd/progress.md\` 添加完成项，记录纯比较模块、三组 Artifact 对和最终 pytest 数量。

- [ ] **Step 3: 完整验证与提交文档**

Run: \`python -m pytest -q\`

Expected: 全部测试通过。

Run: \`python experiments/trace_diff_analysis.py\`

Expected: 生成 3 个稳定排序的案例比较与 \`.loop/runs/trace-diff-analysis/report.json\`。

Run: \`git diff --check\`

Expected: exit code \`0\`。

\`\`\`bash
git add docs/trace-diff-analysis.md docs/experiments.md README.md README.zh-CN.md docs/replay.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain trace diff analysis"
\`\`\`
