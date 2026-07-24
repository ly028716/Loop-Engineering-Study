# 多目标评估实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 从既有确定性基准运行中计算成功率、总成本和平均成功步数的 Pareto 前沿。

**Architecture:** loop_engineering.multi_objective 提供纯支配判断与前沿提取。experiments.multi_objective_evaluation 复用 run_benchmark 的 20 条运行，输出三目标点、前沿和被支配解释。

**Tech Stack:** Python 3.11、标准库 dataclasses/json、pytest。

## Global Constraints

- 不修改 benchmark_suite.py 的加权总分、排名或 Artifact 格式。
- 仅比较五个确定性基准场景与四种策略。
- 不支持权重、归一化、偏好输入或唯一最佳结论。
- 报告写入 .loop/runs/multi-objective-evaluation/report.json，使用 UTF-8、ensure_ascii=False、缩进和末尾换行。
- None 平均成功步数在比较中视为正无穷；完全相同点互不支配。

---

## File Structure

- Create loop_engineering/multi_objective.py：ObjectivePoint、支配关系、前沿和解释。
- Create tests/test_multi_objective.py：支配与边界测试。
- Create experiments/multi_objective_evaluation.py：基准聚合、报告和 CLI。
- Create tests/test_multi_objective_evaluation.py：20 条运行、报告与顺序测试。
- Create docs/multi-objective-evaluation.md：学习说明。
- Modify docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md。

### Task 1: 建立 Pareto 纯领域模块

**Files:**

- Create: tests/test_multi_objective.py
- Create: loop_engineering/multi_objective.py

**Interfaces:**

- Produces: ObjectivePoint、dominates(left, right)、pareto_front(points)、dominated_by(points)。

- [ ] **Step 1: 写入失败测试**

~~~python
from loop_engineering.multi_objective import (
    ObjectivePoint,
    dominated_by,
    dominates,
    pareto_front,
)


def test_dominates_requires_no_worse_and_one_strictly_better_objective() -> None:
    best = ObjectivePoint("best", 1.0, 4.0, 3.0)
    worse = ObjectivePoint("worse", 0.8, 5.0, 4.0)

    assert dominates(best, worse) is True
    assert dominates(worse, best) is False


def test_pareto_front_keeps_non_dominated_and_identical_points() -> None:
    points = (
        ObjectivePoint("tradeoff-success", 1.0, 8.0, 5.0),
        ObjectivePoint("tradeoff-cost", 0.8, 4.0, 3.0),
        ObjectivePoint("dominated", 0.8, 6.0, 4.0),
        ObjectivePoint("identical", 0.8, 4.0, 3.0),
        ObjectivePoint("none-steps", 0.8, 4.0, None),
    )

    assert [item.strategy for item in pareto_front(points)] == [
        "tradeoff-success", "tradeoff-cost", "identical"
    ]
    assert dominated_by(points)["dominated"] == ["tradeoff-cost", "identical"]
    assert dominates(ObjectivePoint("numeric", 0.8, 4.0, 3.0), points[-1]) is True
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_multi_objective.py -q

Expected: ModuleNotFoundError for loop_engineering.multi_objective.

- [ ] **Step 3: 实现最小模型**

定义 frozen ObjectivePoint(strategy, success_rate, total_cost, average_success_steps)。比较键将 None 转为 float("inf")。dominates 检查三个“不差”条件与至少一个严格条件。pareto_front 保留没有其他点支配它的输入点；dominated_by 收集每个被支配点的全部支配者。

- [ ] **Step 4: 验证并提交**

Run: python -m pytest tests/test_multi_objective.py -q

Expected: 2 passed.

~~~bash
git add loop_engineering/multi_objective.py tests/test_multi_objective.py
git commit -m "feat: add pareto multi-objective analysis"
~~~

### Task 2: 聚合基准并持久化报告

**Files:**

- Create: experiments/multi_objective_evaluation.py
- Create: tests/test_multi_objective_evaluation.py

**Interfaces:**

- Consumes: run_benchmark、STRATEGIES、ObjectivePoint、pareto_front、dominated_by。
- Produces: run_multi_objective_evaluation(output_dir: str | Path = ".loop/runs/multi-objective-evaluation") -> dict[str, object]。

- [ ] **Step 1: 写入失败测试**

~~~python
import json
from pathlib import Path

from experiments.multi_objective_evaluation import run_multi_objective_evaluation


def test_evaluation_reuses_benchmark_and_persists_stable_report(tmp_path: Path) -> None:
    result = run_multi_objective_evaluation(tmp_path)

    assert len(result["benchmark_runs"]) == 20
    assert [item["strategy"] for item in result["points"]] == [
        "fixed", "error_aware", "memory_aware", "adaptive"
    ]
    assert set(result["dominated_by"]).issubset(
        {item["strategy"] for item in result["points"]}
    )
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == result
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_multi_objective_evaluation.py -q

Expected: ModuleNotFoundError for experiments.multi_objective_evaluation.

- [ ] **Step 3: 实现聚合与报告**

调用 run_benchmark(root / "benchmark-suite")。对每个 STRATEGIES 项聚合成功比例、所有五条运行 cost 之和、成功运行的 steps 均值（无成功时 None）。转换 ObjectivePoint 后生成 points、pareto_front 和 dominated_by；以 asdict 生成 JSON 负载。报告包含 objectives、points、pareto_front、dominated_by、benchmark_runs，并写入 root/report.json。使用 experiments/_bootstrap.py 直接脚本导入模式，main() 打印 JSON。

- [ ] **Step 4: 验证并提交**

Run: python -m pytest tests/test_multi_objective_evaluation.py -q

Expected: 1 passed.

Run: python experiments/multi_objective_evaluation.py

Expected: 20 条基准运行、4 个目标点、非空 Pareto 前沿和报告。

Run: python -m pytest -q

Expected: 全部测试通过。

~~~bash
git add experiments/multi_objective_evaluation.py tests/test_multi_objective_evaluation.py
git commit -m "feat: add multi-objective evaluation experiment"
~~~

### Task 3: 文档与最终验证

**Files:**

- Create: docs/multi-objective-evaluation.md
- Modify: docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md

- [ ] **Step 1: 创建学习文档**

说明运行命令、三目标方向、Pareto 前沿、被支配解释与不产生唯一最佳的边界。

~~~powershell
python experiments/multi_objective_evaluation.py
~~~

- [ ] **Step 2: 更新导航和进度**

在实验命令列表与两份 README 学习路径加入新文档；进度记录 20 条运行、4 个点、Pareto 前沿和最终 pytest 数量。

- [ ] **Step 3: 最终验证并提交**

Run: python -m pytest -q

Expected: 全部测试通过.

Run: python experiments/multi_objective_evaluation.py

Expected: 默认目录生成报告.

Run: git diff --check

Expected: exit code 0.

~~~bash
git add docs/multi-objective-evaluation.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain multi-objective evaluation"
~~~

