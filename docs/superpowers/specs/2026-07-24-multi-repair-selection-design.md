# 多修复方案选择设计

## 目标

为既有诊断驱动修复学习实验提供多个确定性修复候选。每个候选必须真实重跑、
诊断和保存 Artifact；系统依据成功状态、目标诊断、成本和步数选择最优候选，
并将完整证据写入结构化报告。

该能力用于学习“提出多个修复假设后，如何以运行证据选择方案”。它不是动态
策略搜索、生产自动修复或对外部副作用的重放。

## 范围

### 包含

- 新增纯选择模块 `loop_engineering.repair_selection`。
- 新增 `experiments.multi_repair_selection`，覆盖现有三个诊断修复案例。
- 每个案例声明至少两个候选修复，并分别运行、诊断、度量和持久化。
- 为所有候选、排序、选中理由和基线证据生成 UTF-8 JSON 报告。
- 为排序规则、候选运行、Artifact 与报告添加测试。

### 不包含

- 修改 `LoopRunner`、`diagnose_trace`、`MetricReport` 或 Artifact JSON 格式。
- 搜索未声明的 Action、策略、预算或候选组合。
- 修改既有 `diagnosis_repair_loop.py` 的单修复实验输出契约。
- 将选择结果写回运行时策略或再次执行外部副作用。

## 选择模型

`loop_engineering.repair_selection` 只处理已完成候选的结果，不构建 Runner 或访问
文件系统。

- `RepairCandidateEvaluation` 包含候选名称、声明顺序、成功状态、目标诊断是否
  消除、`MetricReport`、诊断代码与 Artifact 路径。
- `rank_repair_candidates(candidates)` 返回稳定的排序结果。
- `select_best_repair(candidates)` 返回排名第一的候选和由排序维度组成的选择理由。

排序键按以下顺序固定：

1. 修复后 Trace 是否为 `SUCCEEDED`，成功优先。
2. 目标诊断是否全部消除，消除优先。
3. 总成本升序。
4. 执行步数升序。
5. 候选声明顺序升序，用于完全相同时的确定性决胜。

候选评价的“修复成功”要求：修复后成功完成，且修复后诊断代码与目标诊断代码
没有交集。基线是否包含目标诊断仍由实验在案例层验证。

## 候选实验

新增 `experiments/multi_repair_selection.py`。它为每个案例构建一个基线运行，并对
每个候选创建独立 Runner 后真实重跑。候选如下：

| 案例 | 候选名称 | 修复方式 | 预期选择 |
| --- | --- | --- | --- |
| `action_failure` | `replace_action_step_1` | 替换失败 Action，步长 `1.0` | 否 |
| `action_failure` | `replace_action_step_1_5` | 替换失败 Action，步长 `1.5` | 是 |
| `stalled_progress` | `replace_action_step_1` | 替换停滞 Action，步长 `1.0` | 否 |
| `stalled_progress` | `replace_action_step_2` | 替换停滞 Action，步长 `2.0` | 是 |
| `tight_budget` | `restore_budget_step_1` | 恢复为 `8` 步预算，步长 `1.0` | 否 |
| `tight_budget` | `preserve_budget_step_2` | 保持 `3` 步预算，步长 `2.0` | 是 |

所有候选使用正常 `NumericAction`。候选的 Artifact 保存到案例目录，并使用候选名称
区分文件。未知案例或未声明候选必须抛出 `ValueError`。

## 报告

实验按 `action_failure`、`stalled_progress`、`tight_budget` 顺序返回案例记录，并写入：

```text
.loop/runs/multi-repair-selection/report.json
```

每个记录包含：

- `case`、目标诊断代码、基线摘要与基线 Artifact 路径；
- 候选评价列表，按最终排名排列；
- `selected_candidate`、`selection_reason` 与选中候选 Artifact 路径；
- `repair_succeeded`，其值与选中候选的修复成功结论一致。

评价列表和报告键必须稳定，使用 `ensure_ascii=False`、缩进 JSON、UTF-8 与末尾换行。
报告保存失败、Artifact 加载失败等 I/O 错误保持向上传播。

## 测试与验收

测试至少覆盖：

- 成功、目标诊断消除、成本、步数和声明顺序的排序优先级；
- 所有排序键相同的候选仍按声明顺序稳定排序；
- 三个案例均产生两个候选和独立 Artifact；
- 三个预期候选均被选中、成功完成且消除目标诊断；
- 报告可由 `json.loads` 恢复，选中候选与排名第一者一致；
- 既有诊断修复和 Trace 差异分析测试不回归。

验收命令：

```powershell
python -m pytest -q
python experiments/multi_repair_selection.py
```

## 设计边界

选择器只比较已经完成的候选，不负责生成无限候选集。该边界保证学习结果可重放、
成本可解释，并使“选择”与“构建候选运行”保持独立。未来可新增候选注册表或其他
评分维度，但必须显式声明排序顺序，避免隐式或不稳定的选择结果。
