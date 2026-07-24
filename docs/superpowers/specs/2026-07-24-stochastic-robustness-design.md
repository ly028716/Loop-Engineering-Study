# 随机性与鲁棒性实验设计

## 目标

在不改变确定性基线的前提下，评估四种既有策略在随机动作失败与有界数值噪声共同
存在时的鲁棒性。实验必须能通过固定种子完全复现单次运行、Trace 与聚合报告。

## 范围

### 包含

- 新增 `experiments.stochastic_robustness`。
- 使用 `fixed`、`error_aware`、`memory_aware`、`adaptive` 四种策略。
- 为低、中、高扰动档分别运行 8 个固定随机种子。
- 保存 96 次独立运行的 Artifact，并生成结构化统计报告和稳定排序。

### 不包含

- 修改既有确定性实验、策略、`LoopRunner`、`MetricReport` 或 Artifact 格式。
- 使用全局随机状态、外部随机服务或统计显著性检验。
- 搜索或自动调节策略参数。

## 扰动模型

`StochasticAction` 仅用于新实验。每次运行独立接受 `random.Random(seed)`：

1. 每个动作尝试按失败率随机决定是否失败；失败时保留数值，递增状态步骤并标记
   `stochastic_failure`。
2. 成功时对决策增量叠加 `uniform(-noise, noise)`，再应用到数值状态；成本为实际
   增量的绝对值。

扰动档固定为：

| 档位 | 失败率 | 噪声幅度 |
| --- | --- | --- |
| `low` | `0.05` | `0.10` |
| `medium` | `0.15` | `0.30` |
| `high` | `0.30` | `0.60` |

每档使用 8 个声明顺序固定的种子，总运行数为 `3 × 4 × 8 = 96`。失败率必须在
`[0, 1]`，噪声幅度必须非负；不符合时抛出 `ValueError`。目标评估采用合理容差，
避免连续噪声要求精确命中目标。

## 实验与报告

`run_stochastic_robustness(output_dir=".loop/runs/stochastic-robustness")` 以扰动档、
策略、种子顺序执行。每次运行保存一个 Artifact。报告写入：

```text
.loop/runs/stochastic-robustness/report.json
```

原始运行记录包含策略、档位、种子、成功、成本、步数、最终得分和 Artifact 路径。
每个档位/策略组汇总运行数、成功数、成功率、平均/最差/P90 成本、平均/P90 步数。

P90 采用排序样本的 nearest-rank：索引 `ceil(0.90 * n) - 1`。每档排序键固定为：
成功率降序、成本 P90 升序、平均步数升序、策略声明顺序。

报告必须使用 UTF-8、`ensure_ascii=False`、缩进 JSON 与末尾换行，且键和记录顺序
稳定。

## 测试与验收

- 相同配置和种子重跑时 Trace 派生指标完全一致。
- 总共 96 条运行和 96 个 Artifact；每个档位/策略汇总恰好含 8 次运行。
- 汇总统计和排序可 JSON 序列化，顺序稳定。
- 非法失败率或噪声幅度抛出 `ValueError`。
- 现有确定性实验与全量测试不回归。

验收命令：

```powershell
python -m pytest -q
python experiments/stochastic_robustness.py
```

## 解释边界

该实验估计固定扰动模型与有限种子集中的经验鲁棒性，不构成对真实环境分布、长期
可靠性或统计显著性的证明。固定种子用于可复现学习，而非替代更大规模随机评估。
