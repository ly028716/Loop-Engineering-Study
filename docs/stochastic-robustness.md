# 随机性与鲁棒性实验

本实验以固定随机种子评估四种策略在随机动作失败与有界数值噪声下的经验鲁棒性。

## 运行实验

```powershell
python experiments/stochastic_robustness.py
```

报告写入 `.loop/runs/stochastic-robustness/report.json`，并保存每次运行的 Artifact。

## 扰动矩阵

实验运行低、中、高三档扰动，每档覆盖 `fixed`、`error_aware`、`memory_aware`、`adaptive` 四种策略及 8 个固定种子，共 96 次运行。

## 如何阅读报告

每组汇总包含成功率、平均/最差/P90 成本与平均/P90 步数。每个档位的排名优先成功率，再比较成本 P90、平均步数和策略声明顺序。

## 解释边界

结果仅描述固定扰动模型和有限种子集下的经验表现，不构成真实环境分布或统计显著性的证明。
