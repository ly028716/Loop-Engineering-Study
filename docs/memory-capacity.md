# Memory capacity comparison

这个实验研究一个具体问题：历史事件窗口的大小，如何影响循环对失败的记忆和恢复？

当前 `WorkingMemory` 保存的是有序事件，不是抽象的“记忆条目”。因此容量使用事件
数量表示。一个完整循环通常包含 `OBSERVE`、`DECIDE`、`ACT`、`EVALUATE` 和
`FEEDBACK`，策略在下一轮的 `OBSERVE` 之后读取历史，所以容量 7 大致代表一个可
观察循环窗口。

## 四种配置

| 配置 | 容量 | 策略可见范围 |
| --- | ---: | --- |
| `no_memory` | 1 | 策略显式忽略历史事件，只看当前状态。 |
| `short_memory` | 7 | 大约保留最近一个循环窗口。 |
| `working_memory` | 21 | 大约保留最近三个循环窗口。 |
| `long_window` | 1000 | 覆盖本次运行的完整历史。 |

实验在第 1 次和第 4 次 Action 调用时注入失败。`MemoryRecoveryPolicy` 如果在可见
事件中找到失败的 `ACT`，就选择 `2.0` 的增量，否则选择 `1.0`。这样可以观察短窗口
何时遗忘早期失败，以及长窗口是否会持续影响后续决策。

## 运行

```powershell
python experiments/memory_capacity.py
```

脚本输出四条 JSON 结果，并在 `.loop/runs/memory-capacity/` 下生成四个 Artifact。
运行产物已被 `.gitignore` 忽略。

重点比较：

- `steps`：达到目标需要的循环轮数；
- `failure_count`：失败动作数量，应该与失败计划一致；
- `recovery_action_count`：策略选择更大增量的次数；
- `final_score` 与 `success`：最终结果；
- `stop_reason`：循环为何结束。

## 检查记忆可见性

```python
from loop_engineering.artifacts import load_run_artifact

trace, report = load_run_artifact(
    ".loop/runs/memory-capacity/short_memory.json"
)
failed_actions = [
    event for event in trace.events
    if event.phase == "ACT" and event.payload.get("success") is False
]
print(report.steps, report.success)
print([(event.step, event.payload) for event in failed_actions])
```

进一步检查相邻的 `OBSERVE`、`DECIDE` 和 `ACT` 事件，可以判断失败事件是否仍在策略
读取窗口中。这个实验说明的是确定性事件记忆的边界，不代表通用 Agent 或 LLM 的
长期记忆能力，也不包含跨运行持久化。
