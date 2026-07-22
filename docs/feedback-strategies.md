# Feedback strategy comparison

这个实验回答一个具体问题：评估结果和最近事件是否真的会改变下一轮循环决策？

三种策略使用相同的初始状态、Action、Evaluator 和停止条件，唯一变化是策略读取
的输入：

| 策略 | 使用的输入 | 作用 |
| --- | --- | --- |
| `fixed` | 当前状态 | 每轮增加 `1.0`，作为无反馈基线。 |
| `error_aware` | 上一轮 `Feedback.absolute_error` | 距离目标较远时增加 `2.0`，验证评估反馈是否加快收敛。 |
| `memory_aware` | 最近 `LoopEvent` | 观察失败动作或停滞评估，验证记忆是否能影响策略。 |

## 运行

```powershell
python experiments/feedback_strategies.py
```

脚本输出一个 JSON 数组，并在 `.loop/runs/feedback-strategies/` 下为每种策略写入
一个 Artifact。运行产物已被 `.gitignore` 忽略，不应提交到 Git。

## 如何比较

- `steps`：达到目标需要多少轮；越小表示当前实验中的收敛更快。
- `final_score`：最后一轮评估得分；需要结合 `success` 一起看。
- `cost`：Action 成本之和；失败动作的成本也会体现在 Trace 中。
- `average_step_gain`：评估得分的平均变化，用于观察是否持续改善。
- `stop_reason`：明确说明是成功、最大步数还是其他条件触发了停止。

预期上，`fixed` 会稳定但步数较多；`error_aware` 会利用上一轮评估结果扩大步长；
`memory_aware` 会读取一次注入失败的 `ACT` 事件，并在后续决策中使用更大的步长。
这些结论只适用于当前确定性实验，不代表通用 Agent 或 LLM 性能。

## 查看 Artifact

```python
from loop_engineering.artifacts import load_run_artifact

trace, report = load_run_artifact(
    ".loop/runs/feedback-strategies/memory_aware.json"
)
print(report.steps, report.success, report.final_score)
print([(event.step, event.phase) for event in trace.events])
```

查看 `DECIDE` 和 `FEEDBACK` 事件，可以直接确认策略的输入和下一步动作是否发生了
变化。Artifact 是一次运行的证据和可恢复 Trace，不会重新执行 Action。
