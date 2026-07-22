# Memory Capacity Comparison Design

## Goal

增加一个确定性的记忆容量对比实验，研究不同历史事件窗口如何影响循环对失败的
识别、恢复动作和最终收敛结果。

## Scope

本阶段只新增实验、测试和学习文档，不修改 `LoopRunner`、`WorkingMemory`、Artifact
格式或现有 CLI 行为。每种记忆配置都使用独立的 Runner、Policy、Action 和
`WorkingMemory`，避免运行之间共享状态。

## Controlled experiment

所有配置使用相同的：

- 初始状态：`step=0`、`value=0.0`、`goal=6.0`
- Evaluator：`GoalEvaluator(tolerance=0.0)`
- Stop Conditions：`SuccessReached()`、`MaxSteps(12)`
- Action：同一个确定性失败计划，在第 1 次和第 4 次 Action 调用时返回失败，其余调用正常增加数值
- Artifact 根目录：`.loop/runs/memory-capacity/`

记忆配置定义如下：

| 配置 | 策略历史输入 | 事件容量 | 实验目的 |
| --- | --- | ---: | --- |
| `no_memory` | 策略忽略 `recent_events` | 1 | 无历史输入基线 |
| `short_memory` | 最近约 1 个循环窗口 | 7 | 观察短期记忆的即时恢复 |
| `working_memory` | 最近约 3 个循环窗口 | 21 | 观察中等窗口对重复失败的保留 |
| `long_window` | 完整运行窗口 | 1000 | 观察长期保留历史事件的效果 |

`MemoryRecoveryPolicy` 在 `recent_events` 中发现失败的 `ACT` 事件时选择增量
`2.0`，否则选择 `1.0`。`no_memory` 使用同一策略类型但显式忽略历史输入，确保
差异来自记忆可见性而不是不同的动作规则。

## Experiment output

入口为 `experiments/memory_capacity.py`。脚本依次运行四种配置，分别保存完整
Artifact，并输出一个 JSON 数组。每条结果包含：

- `memory_mode`
- `capacity`
- `steps`
- `success`
- `final_score`
- `failure_count`
- `recovery_action_count`
- `stop_reason`
- `artifact_path`

实验重点不是证明某一种容量永远最好，而是让“记忆窗口可见范围”与行为结果之间的
关系可以从事件 Trace 和统一指标中直接观察。

## Learning documentation

新增 `docs/memory-capacity.md`，说明：

- 为什么用无记忆配置作为基线；
- `WorkingMemory` 的容量单位是事件，不是抽象轮次；
- 四种配置的差异与预期观察；
- 如何比较失败次数、恢复动作、步数和停止原因；
- 如何从 Artifact 检查记忆可见的 `ACT` 事件；
- 当前实验不代表通用 Agent 或 LLM 的长期记忆能力。

同时更新 `docs/experiments.md`、中英文 README 和进度记录。

## Testing

新增 `tests/test_memory_capacity.py`，覆盖：

- 失败计划只在第 1 次和第 4 次 Action 调用失败；
- `MemoryRecoveryPolicy` 在看见失败 `ACT` 时选择 `2.0`；
- `no_memory` 不读取历史事件；
- 四种配置都能完成实验并生成 Artifact；
- 每个 Artifact 都能通过 `load_run_artifact()` 恢复；
- 结果字段、失败次数和恢复动作次数符合实验契约；
- 现有测试保持通过。

验证命令：

```powershell
python -m pytest -q
python experiments/memory_capacity.py
```

## Non-goals

- 不新增跨运行长期记忆或数据库存储。
- 不压缩、总结或语义检索历史事件。
- 不引入 LLM、网络调用、异步调度或通用 benchmark 框架。
- 不改变现有 `WorkingMemory` API 和 Artifact JSON 结构。
- 不提交 `.loop/runs/memory-capacity/` 下的运行产物。

## Acceptance criteria

- 实验可以从仓库根目录直接运行。
- 四种配置只通过记忆可见范围产生差异，共享同一失败计划、Evaluator 和停止协议。
- Trace 能够显示失败事件是否仍在策略可见窗口内。
- 完整 pytest 测试通过，Artifact 可加载，运行产物保持被 Git 忽略。
