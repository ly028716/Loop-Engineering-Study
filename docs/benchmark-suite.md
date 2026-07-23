# Loop Engineering 评测基准

评测基准将多个确定性场景组合为统一矩阵，用同一套指标比较不同策略。它用于解释本项目中的策略差异，而不是对真实生产环境作出通用性能结论。

## 场景矩阵

基准依次运行 `steady_progress`、`action_failure`、`missing_feedback`、
`stalled_progress` 与 `tight_budget` 五个场景，并让 `fixed`、`error_aware`、
`memory_aware` 和 `adaptive` 四种策略分别执行。

- `steady_progress`：没有故障，观察正常推进效率。
- `action_failure`：第 2 次动作失败，观察恢复决策。
- `missing_feedback`：动作失败但评估反馈不提供恢复信号。
- `stalled_progress`：动作不改变状态，观察安全停止。
- `tight_budget`：仅允许 3 个步骤，观察预算内完成能力。

## 指标与评分

每个策略的总分范围为 0 到 100：

| 指标 | 权重 | 含义 |
| --- | ---: | --- |
| 成功率 | 50 | 成功场景在 5 个场景中的比例。 |
| 步骤效率 | 25 | 成功时相对该场景最少步骤的效率。 |
| 恢复能力 | 15 | 在两个失败相关场景中成功且使用恢复决策的比例。 |
| 预算遵守度 | 10 | 在场景步骤预算内停止的比例。 |

排行榜先按总分降序，再按平均成功步骤数升序，最后按策略名称升序排列。

## 运行基准

```powershell
python experiments/benchmark_suite.py
```

脚本输出场景明细、策略汇总和排行榜，并将 20 份完整 Artifact 写入
`.loop/runs/benchmark-suite/`。Artifact 可使用
`loop_engineering.artifacts.load_run_artifact()` 回放。

## 阅读排行榜

总分应与场景明细一起阅读。成功率表示完成能力，步骤效率表示完成速度，恢复能力表示失败后是否采取可观测恢复决策，预算遵守度表示停止是否受控。

在当前固定矩阵中，`adaptive` 的恢复模式可在动作失败场景中留下 Trace 证据，因此其总分高于 `fixed`。该结论只适用于本基准的确定性配置。

## 解释边界

基准不包含随机任务、并发执行、外部模型或真实服务故障。新增策略或场景时，应保留固定顺序、可加载 Artifact 和明确的评分规则，避免排行榜失去可重复性。
