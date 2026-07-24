# 随机性与鲁棒性实验实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 用固定种子评估四种策略在随机失败和数值噪声下的经验鲁棒性。

**Architecture:** 新实验模块在本地定义 StochasticAction，并为每个扰动档、策略和种子构建独立随机源与 Runner。它保存原始 Artifact，并将固定统计口径和稳定排序写入 JSON。

**Tech Stack:** Python 3.11、标准库 random/statistics/json、pytest。

## Global Constraints

- 不修改确定性实验、策略、LoopRunner、MetricReport 或 Artifact 格式。
- 使用四种策略、三档扰动、每档八种子，总共 96 次运行。
- 禁止全局随机状态；相同配置/种子必须复现相同结果。
- 报告写入 .loop/runs/stochastic-robustness/report.json，使用 UTF-8、ensure_ascii=False、缩进与末尾换行。
- 排序按成功率降序、成本 P90 升序、平均步数升序、策略声明顺序。

---

## File Structure

- Create experiments/stochastic_robustness.py：随机 Action、运行矩阵、汇总统计、排序与 CLI。
- Create tests/test_stochastic_robustness.py：可复现、参数校验、96 次矩阵和报告测试。
- Create docs/stochastic-robustness.md：学习者说明。
- Modify docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md：导航和进度。

### Task 1: 先定义随机 Action 的契约

**Files:**

- Create: tests/test_stochastic_robustness.py
- Create: experiments/stochastic_robustness.py

**Interfaces:**

- Produces: StochasticAction(failure_rate: float, noise_amplitude: float, rng: random.Random)。
- Consumes: Action、ActionResult、LoopState、Decision。

- [ ] **Step 1: 写入失败测试**

~~~python
import random

import pytest

from experiments.stochastic_robustness import StochasticAction
from loop_engineering.models import LoopState
from loop_engineering.policies import Decision


def test_stochastic_action_is_reproducible_for_the_same_seed() -> None:
    decision = Decision(name="increment", parameters={"amount": 1.0})
    first = StochasticAction(0.15, 0.30, random.Random(101))
    second = StochasticAction(0.15, 0.30, random.Random(101))

    first_results = [first.apply(LoopState(0, 0.0, 6.0), decision) for _ in range(3)]
    second_results = [second.apply(LoopState(0, 0.0, 6.0), decision) for _ in range(3)]

    assert first_results == second_results


@pytest.mark.parametrize("failure_rate,noise", [(-0.01, 0.1), (1.01, 0.1), (0.1, -0.1)])
def test_stochastic_action_rejects_invalid_parameters(failure_rate, noise) -> None:
    with pytest.raises(ValueError):
        StochasticAction(failure_rate, noise, random.Random(1))
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_stochastic_robustness.py -q

Expected: ModuleNotFoundError for experiments.stochastic_robustness.

- [ ] **Step 3: 实现最小随机 Action**

定义失败率和噪声幅度校验。apply 使用该实例 rng：若 rng.random() 小于失败率，返回 state.with_value(state.value, stochastic_failure=True)、success=False、cost=0.0；否则读取 decision.parameters["amount"]，加 rng.uniform(-noise_amplitude, noise_amplitude)，并以实际增量更新状态，cost=abs(actual_amount)。

- [ ] **Step 4: 验证 GREEN 状态并提交**

Run: python -m pytest tests/test_stochastic_robustness.py -q

Expected: 4 passed.

~~~bash
git add experiments/stochastic_robustness.py tests/test_stochastic_robustness.py
git commit -m "feat: add reproducible stochastic action"
~~~

### Task 2: 构建 96 次鲁棒性矩阵和统计报告

**Files:**

- Modify: experiments/stochastic_robustness.py
- Modify: tests/test_stochastic_robustness.py

**Interfaces:**

- Produces: run_stochastic_robustness(output_dir: str | Path = ".loop/runs/stochastic-robustness") -> dict[str, object]。
- Consumes: FixedPolicy、ErrorAwarePolicy、MemoryAwarePolicy、AdaptivePolicy、RecoveryAwareEvaluator、MetricReport、save_run_artifact。

- [ ] **Step 1: 写入失败的实验测试**

~~~python
import json
from pathlib import Path

from experiments.stochastic_robustness import run_stochastic_robustness


def test_robustness_matrix_is_complete_reproducible_and_persisted(tmp_path: Path) -> None:
    first = run_stochastic_robustness(tmp_path / "first")
    second = run_stochastic_robustness(tmp_path / "second")

    assert len(first["runs"]) == 96
    assert first["levels"] == ["low", "medium", "high"]
    assert first["strategies"] == ["fixed", "error_aware", "memory_aware", "adaptive"]
    assert len(first["summaries"]) == 12
    assert all(item["run_count"] == 8 for item in first["summaries"])
    assert [item["success"] for item in first["runs"]] == [
        item["success"] for item in second["runs"]
    ]
    assert json.loads((tmp_path / "first" / "report.json").read_text(encoding="utf-8")) == first
~~~

- [ ] **Step 2: 确认 RED 状态**

Run: python -m pytest tests/test_stochastic_robustness.py -q

Expected: 新增测试失败，因为 run_stochastic_robustness 尚未定义。

- [ ] **Step 3: 实现运行矩阵**

声明 STRATEGIES=(fixed,error_aware,memory_aware,adaptive)，SEEDS 的 8 个固定整数，以及 LEVELS：

~~~python
LEVELS = (
    ("low", 0.05, 0.10),
    ("medium", 0.15, 0.30),
    ("high", 0.30, 0.60),
)
~~~

每个 level/strategy/seed 创建新的 random.Random(seed)、StochasticAction、策略和 LoopRunner；目标为 6.0，预算为 8，GoalEvaluator 的 tolerance 为 0.25。保存 {level}--{strategy}--{seed}.json，记录策略、档位、种子、成功、成本、步数、最终得分与 artifact_path。

- [ ] **Step 4: 实现汇总与排序**

实现 nearest_rank(values, quantile)：对排序后的非空样本返回 ceil(quantile * len(values)) - 1 的元素。每个 level/strategy 汇总 run_count、success_count、success_rate、mean_cost、worst_cost、cost_p90、mean_steps、steps_p90。按全局约束的排序键生成每档 ranking，并返回 levels、strategies、runs、summaries、rankings。将完整结果保存为 report.json。

- [ ] **Step 5: 验证并提交**

Run: python -m pytest tests/test_stochastic_robustness.py -q

Expected: 5 passed.

Run: python experiments/stochastic_robustness.py

Expected: 96 条运行记录、12 条汇总和三个稳定排序。

Run: python -m pytest -q

Expected: 全部测试通过。

~~~bash
git add experiments/stochastic_robustness.py tests/test_stochastic_robustness.py
git commit -m "feat: add stochastic robustness experiment"
~~~

### Task 3: 文档与最终验证

**Files:**

- Create: docs/stochastic-robustness.md
- Modify: docs/experiments.md、README.md、README.zh-CN.md、docs/superpowers/sdd/progress.md

- [ ] **Step 1: 创建学习文档**

创建 docs/stochastic-robustness.md，说明运行命令、低中高扰动档、固定种子、96 次矩阵、成功率与 P90 的含义，以及实验边界。

~~~powershell
python experiments/stochastic_robustness.py
~~~

- [ ] **Step 2: 更新导航**

在 experiments.md 中加入新命令和文档链接；两份 README 学习路径加入该文档；进度文档记录 96 Artifact、12 汇总和最终测试数。

- [ ] **Step 3: 最终验证并提交**

Run: python -m pytest -q

Expected: 全部测试通过。

Run: python experiments/stochastic_robustness.py

Expected: 生成默认报告与 Artifact。

Run: git diff --check

Expected: exit code 0.

~~~bash
git add docs/stochastic-robustness.md docs/experiments.md README.md README.zh-CN.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain stochastic robustness experiment"
~~~

