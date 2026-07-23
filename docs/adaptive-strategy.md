# 自适应策略与预算分配

这个实验比较策略如何使用错误、事件记忆和剩余预算来选择下一步增量。四种策略共享
相同的初始状态、目标、评估器和 `MaxSteps(8)` 安全预算，因此结果差异只来自决策
方式。

## 学习目标

理解可观察的控制信号如何改变循环决策，并在安全预算内比较收敛效率。实验要求
`adaptive` 的 `steps` 少于 `fixed`，同时四种策略都保留完整的可回放证据。

## 控制信号

`FailOnSecondAction` 会在第二次 Action 尝试时确定性地失败一次。失败不改变数值状态，
成本为 `0.0`，但 `RecoveryAwareEvaluator` 会把 Action 是否成功写入
`Feedback.action_success`。这让策略可以区分正常推进与恢复场景。

自适应策略把模式写入 `Decision.parameters.mode_code`，保持参数为数值类型：

| 模式代码 | 模式 | 选择条件 | 增量 |
| ---: | --- | --- | ---: |
| `1.0` | `fast` | 无失败且距离目标较远 | `4.0` |
| `2.0` | `careful` | 剩余距离不超过 `2.0` | `1.0` |
| `3.0` | `recovery` | 上一轮 Action 失败 | `1.0` |
| `4.0` | `budget_guard` | 已使用至少 6 步 | `1.0` |

`mode_code` 是 Trace 中可计数的数值控制信号，而不是字符串状态。`switch_count`
统计相邻自适应决策的模式代码变化次数；`recovery_count` 统计代码为 `3.0` 的决策次数。

## 四种策略

| 策略 | 读取的输入 | 行为 |
| --- | --- | --- |
| `fixed` | 当前状态 | 每轮最多增加 `1.0`。 |
| `error_aware` | `Feedback.absolute_error` | 误差大于 `2.0` 时每轮最多增加 `4.0`。 |
| `memory_aware` | 最近 `ACT` 事件 | 看到失败的 Action 后每轮最多增加 `4.0`。 |
| `adaptive` | 失败反馈、剩余距离和已用步数 | 在 `fast`、`careful`、`recovery` 与 `budget_guard` 间切换。 |

## 运行实验

在 PowerShell 中运行：

```powershell
python experiments/adaptive_strategy.py
```

脚本按 `fixed`、`error_aware`、`memory_aware`、`adaptive` 的顺序输出 4 条 JSON 结果，
并将 Artifact 保存到 `.loop/runs/adaptive-strategy/`。每条结果包含 `steps`、
`switch_count`、`recovery_count`、成功状态、停止原因和 Artifact 路径。

## 阅读结果

先比较 `steps`：较小的值表示在本实验的共同安全预算内使用了更少循环轮数。然后检查
`success`、`final_score` 和 `stop_reason`，确认更快的结果没有以跳过成功判定为代价。

`switch_count` 和 `recovery_count` 仅对 `adaptive` 有意义；其他策略固定为 `0`，因为它们
不产生 `mode_code`。可使用 `loop_engineering.artifacts.load_run_artifact()` 重新加载
`.loop/runs/adaptive-strategy/adaptive.json`，检查 `DECIDE` 事件中的数值模式代码以及
失败 `ACT` 之后的恢复决策。Artifact 会重放已保存的 Trace 和指标，不会重新执行
Action。

## 可继续探索的问题

- 不同目标距离和失败位置会怎样改变模式切换次数？
- `budget_guard` 的阈值如何影响安全预算耗尽前的保守程度？
- 如何在不牺牲可回放 Trace 的前提下，为控制信号引入更多可验证的成本模型？
