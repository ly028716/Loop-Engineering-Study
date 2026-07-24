# 多目标评估设计

## 目标

基于既有五场景、四策略确定性基准，以成功率、总成本和平均成功步数三个目标
进行 Pareto 分析。实验展示不可兼得的策略权衡，不使用权重把多个目标压缩为唯一
“最佳”结论。

## 范围

### 包含

- 新增纯领域模块 `loop_engineering.multi_objective`。
- 新增 `experiments.multi_objective_evaluation`，复用 `run_benchmark` 的 20 条运行。
- 聚合四种策略的三目标点，输出 Pareto 前沿与被支配解释。
- 保存 UTF-8 JSON 报告并提供测试与学习文档。

### 不包含

- 修改 `benchmark_suite.py` 的加权总分、排名或 Artifact 格式。
- 权重、归一化、偏好输入或唯一最优策略选择。
- 随机鲁棒性结果或其他实验数据的联合比较。

## Pareto 模型

`ObjectivePoint` 包含策略名称、成功率、总成本、平均成功步数。

`dominates(left, right)` 仅在以下条件同时满足时返回真：

1. `left.success_rate >= right.success_rate`；
2. `left.total_cost <= right.total_cost`；
3. `left.average_success_steps <= right.average_success_steps`；
4. 至少一项严格更优。

`pareto_front(points)` 返回输入声明顺序中的全部非支配点。完全相同的点互不支配。
没有成功运行时，`average_success_steps` 为 `None`；在比较中视作正无穷，任何数值
步数都优于它。

`dominated_by(points)` 为每个被支配策略返回全部支配者名称，按输入声明顺序排列。

## 实验与报告

`run_multi_objective_evaluation(output_dir=".loop/runs/multi-objective-evaluation")`
调用 `run_benchmark`，并从其五个场景、四种策略、20 条运行中计算：

- 成功率：成功运行数除以五；
- 总成本：五条运行的成本之和；
- 平均成功步数：成功运行的步数平均值，无成功时为 `None`。

报告写入 `.loop/runs/multi-objective-evaluation/report.json`，包含目标方向、所有点、
Pareto 前沿、被支配解释和原始 `benchmark_runs`。报告键与策略顺序稳定，使用 UTF-8、
`ensure_ascii=False`、缩进 JSON 与末尾换行。

## 测试与验收

- 严格支配、互不支配、完全相同和 `None` 步数边界。
- 实验恰好复用 20 条运行并生成 4 个策略点。
- 前沿和被支配解释顺序稳定、可由 `json.loads` 恢复。
- 既有基准和全量 pytest 不回归。

验收命令：

```powershell
python -m pytest -q
python experiments/multi_objective_evaluation.py
```

## 解释边界

Pareto 前沿只说明在声明的三个目标中没有其他策略同时更好；它不代表某个前沿策略
在所有业务偏好下都更合适。若需要唯一选择，应在未来显式引入偏好，而非隐式改变
Pareto 规则。
