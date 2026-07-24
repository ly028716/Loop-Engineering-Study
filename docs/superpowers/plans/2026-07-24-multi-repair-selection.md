# 多修复方案选择实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 为三组诊断修复案例重跑多个候选方案，并基于成功、诊断、成本和步数选择最优方案。

**Architecture:** loop_engineering.repair_selection 是只处理完成候选结果的纯排序模块。experiments.multi_repair_selection 构建基线和候选 Runner，保存每条证据并将排名、选择结果写入 JSON 报告。

**Tech Stack:** Python 3.11、标准库 dataclasses/json、pytest。

## Global Constraints

- 不添加依赖，不修改 LoopRunner、diagnose_trace、MetricReport 或 Artifact JSON 格式。
- 仅处理 action_failure、stalled_progress、tight_budget，并保持该顺序。
- 排序顺序固定为：成功、目标诊断消除、低成本、少步数、声明顺序。
- 每个候选必须真实运行、诊断并保存独立 Artifact；不搜索未声明候选。
- 不改变 experiments.diagnosis_repair_loop 的现有输出契约。
- 报告使用 UTF-8、ensure_ascii=False、缩进 JSON 和末尾换行，保存在 .loop/runs/multi-repair-selection/report.json。

---

## File Structure

- Create loop_engineering/repair_selection.py：候选评价模型、稳定排序和选择理由。
- Create tests/test_repair_selection.py：纯选择器排序优先级测试。
- Create experiments/multi_repair_selection.py：三案例候选构建、运行、诊断、Artifact 与 JSON 报告。
- Create tests/test_multi_repair_selection.py：实验、Artifact、报告和选择结果测试。
- Create docs/multi-repair-selection.md：学习者说明。
- Modify docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md：加入导航与进度。

### Task 1: 实现稳定候选排序器

**Files:**

- Create: loop_engineering/repair_selection.py
- Create: tests/test_repair_selection.py

**Interfaces:**

- Produces: RepairCandidateEvaluation、RepairSelection、rank_repair_candidates(candidates)、select_best_repair(candidates)。
- Consumes: MetricReport。

- [ ] **Step 1: 写入失败测试**

~~~python
from loop_engineering.metrics import MetricReport
from loop_engineering.repair_selection import (
    RepairCandidateEvaluation,
    rank_repair_candidates,
    select_best_repair,
)


def _candidate(name, index, succeeded=True, eliminated=True, cost=3.0, steps=3):
    return RepairCandidateEvaluation(
        name=name,
        declaration_index=index,
        succeeded=succeeded,
        target_diagnostics_eliminated=eliminated,
        metrics=MetricReport(steps, 1.0, succeeded, cost, 0.0),
        diagnostic_codes=(),
        artifact_path=f"/tmp/{name}.json",
    )


def test_rank_uses_declared_priority() -> None:
    ranked = rank_repair_candidates((
        _candidate("failed", 0, succeeded=False, cost=0.0, steps=0),
        _candidate("diagnostic-remains", 1, eliminated=False, cost=0.0, steps=0),
        _candidate("expensive", 2, cost=5.0, steps=1),
        _candidate("slow", 3, cost=3.0, steps=5),
        _candidate("best", 4, cost=3.0, steps=3),
    ))
    assert [item.name for item in ranked] == [
        "best", "slow", "expensive", "diagnostic-remains", "failed"
    ]


def test_select_preserves_declaration_order_for_exact_ties() -> None:
    selection = select_best_repair((
        _candidate("declared-first", 0),
        _candidate("declared-second", 1),
    ))
    assert selection.selected.name == "declared-first"
    assert "declaration order" in selection.reason
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_repair_selection.py -q

Expected: collection fails with ModuleNotFoundError for loop_engineering.repair_selection.

- [ ] **Step 3: 写入最小实现**

~~~python
@dataclass(frozen=True)
class RepairCandidateEvaluation:
    name: str
    declaration_index: int
    succeeded: bool
    target_diagnostics_eliminated: bool
    metrics: MetricReport
    diagnostic_codes: tuple[str, ...]
    artifact_path: str


@dataclass(frozen=True)
class RepairSelection:
    selected: RepairCandidateEvaluation
    reason: str


def _rank_key(item: RepairCandidateEvaluation) -> tuple[object, ...]:
    return (
        not item.succeeded,
        not item.target_diagnostics_eliminated,
        item.metrics.cost,
        item.metrics.steps,
        item.declaration_index,
    )
~~~

让 rank_repair_candidates 返回 tuple(sorted(candidates, key=_rank_key))。输入为空时 select_best_repair 抛出 ValueError("At least one repair candidate is required.")；否则返回排名第一项和包含五个排序维度的英文理由。

- [ ] **Step 4: 验证 GREEN 状态并提交**

Run: python -m pytest tests/test_repair_selection.py -q

Expected: 2 passed.

~~~bash
git add loop_engineering/repair_selection.py tests/test_repair_selection.py
git commit -m "feat: add repair candidate selection"
~~~

### Task 2: 运行并选择三组修复候选

**Files:**

- Create: experiments/multi_repair_selection.py
- Create: tests/test_multi_repair_selection.py

**Interfaces:**

- Consumes: diagnose_trace、save_run_artifact、MetricReport.from_trace、RepairCandidateEvaluation、select_best_repair，以及诊断修复实验的案例常量和基线构建逻辑。
- Produces: run_multi_repair_selection(output_dir: str | Path = ".loop/runs/multi-repair-selection") -> list[dict[str, object]]。

- [ ] **Step 1: 写入失败的实验测试**

~~~python
import json
from pathlib import Path

from experiments.multi_repair_selection import run_multi_repair_selection
from loop_engineering.artifacts import load_run_artifact


def test_selection_persists_candidates_and_selects_expected(tmp_path: Path) -> None:
    results = run_multi_repair_selection(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure", "stalled_progress", "tight_budget"
    ]
    assert [item["selected_candidate"] for item in results] == [
        "replace_action_step_1_5",
        "replace_action_step_2",
        "preserve_budget_step_2",
    ]
    for item in results:
        assert len(item["candidates"]) == 2
        assert item["repair_succeeded"] is True
        assert item["candidates"][0]["name"] == item["selected_candidate"]
        assert item["candidates"][0]["succeeded"] is True
        trace, _ = load_run_artifact(item["selected_artifact_path"])
        assert trace.final_state is not None
        assert trace.final_state.status == "SUCCEEDED"
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == results


def test_selection_is_stable(tmp_path: Path) -> None:
    first = run_multi_repair_selection(tmp_path / "first")
    second = run_multi_repair_selection(tmp_path / "second")
    assert [item["selected_candidate"] for item in first] == [
        item["selected_candidate"] for item in second
    ]
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_multi_repair_selection.py -q

Expected: collection fails with ModuleNotFoundError for experiments.multi_repair_selection.

- [ ] **Step 3: 声明候选并实现真实重跑**

采用 trace_diagnostics.py 的 _bootstrap.py 直跑导入约定。重用 diagnosis_repair_loop.py 的 CASES、TARGET_CODES、_build_baseline 和 _summary。

~~~python
CANDIDATES = {
    "action_failure": (
        ("replace_action_step_1", 1.0, 4),
        ("replace_action_step_1_5", 1.5, 4),
    ),
    "stalled_progress": (
        ("replace_action_step_1", 1.0, 8),
        ("replace_action_step_2", 2.0, 8),
    ),
    "tight_budget": (
        ("restore_budget_step_1", 1.0, 8),
        ("preserve_budget_step_2", 2.0, 3),
    ),
}
~~~

每项用 IncrementPolicy、NumericAction、GoalEvaluator(tolerance=0.0)、SuccessReached 和 MaxSteps 创建 Runner。action_failure 初始状态为 LoopState(step=0, value=0.0, goal=3.0)；其余案例的目标为 6.0。每个候选运行后保存 {case}.{candidate_name}.artifact.json，计算诊断代码与目标诊断消除状态，再创建 RepairCandidateEvaluation。基线保存为 {case}.baseline.artifact.json。未知案例或候选为空时抛出 ValueError。

- [ ] **Step 4: 构建稳定报告和 CLI**

对评价列表调用 rank_repair_candidates，使用 asdict 生成候选 payload，并把 diagnostic_codes 转为列表。每个案例记录必须包含 case、target_diagnostic_codes、baseline、baseline_artifact_path、candidates、selected_candidate、selected_artifact_path、selection_reason、repair_succeeded。以 _save_report(root / "report.json", results) 写入 JSON；main() 打印 run_multi_repair_selection() 的 JSON。

- [ ] **Step 5: 验证实验并提交**

Run: python -m pytest tests/test_multi_repair_selection.py -q

Expected: 2 passed.

Run: python experiments/multi_repair_selection.py

Expected: 三个选中候选依次为 replace_action_step_1_5、replace_action_step_2、preserve_budget_step_2。

Run: python -m pytest -q

Expected: 全部测试通过。

~~~bash
git add experiments/multi_repair_selection.py tests/test_multi_repair_selection.py
git commit -m "feat: add multi-repair selection experiment"
~~~

### Task 3: 文档和最终验证

**Files:**

- Create: docs/multi-repair-selection.md
- Modify: docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md

- [ ] **Step 1: 创建学习者说明**

创建 docs/multi-repair-selection.md，包含“运行实验”“排序规则”“如何阅读报告”“解释边界”四节，以及：

~~~powershell
python experiments/multi_repair_selection.py
~~~

说明三个案例、每案两个候选、五级排序规则和选择器不会搜索未声明候选或修改运行时策略。

- [ ] **Step 2: 更新导航与进度**

在 docs/experiments.md 的 diagnosis_repair_loop.py 与 trace_diff_analysis.py 命令之间加入新命令和文档链接。在两份 README 学习路径中将多修复方案选择放在诊断修复闭环之后。向进度文档添加候选数量、三个案例、报告和最终 pytest 数量。

- [ ] **Step 3: 完成验证与提交**

Run: python -m pytest -q

Expected: 全部测试通过.

Run: python experiments/multi_repair_selection.py

Expected: 每个选中候选成功并消除目标诊断，生成稳定报告.

Run: git diff --check

Expected: exit code 0.

~~~bash
git add docs/multi-repair-selection.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain multi-repair selection"
~~~

