# Feedback Strategy Comparison Design

## Goal

为 Loop Engineering Study 增加一个可复现的反馈策略对比实验，验证评估反馈和
最近事件记忆是否会改变下一轮决策，并用统一指标比较不同策略的收敛表现。

## Scope

本阶段只新增实验、测试和学习文档，不改变 `LoopRunner`、Artifact 格式或现有
CLI 行为。所有策略使用相同的初始状态、Action、Evaluator 和停止条件；每个策略
独立创建自己的 Runner 和 `WorkingMemory`，避免实验之间共享状态。

## Experiment design

实验入口为 `experiments/feedback_strategies.py`，固定配置如下：

- 初始状态：`step=0`、`value=0.0`、`goal=6.0`
- Action：`NumericAction`
- Evaluator：`GoalEvaluator(tolerance=0.0)`
- Stop Conditions：`SuccessReached()`、`MaxSteps(10)`
- Artifact 目录：`.loop/runs/feedback-strategies/`

实验比较三种策略：

1. `fixed`：每轮增加 `1.0`，忽略反馈和最近事件，作为无反馈基线。
2. `error_aware`：读取上一轮反馈中的 `absolute_error`，当目标距离较大时使用
   `2.0`，否则使用不超过剩余距离的 `1.0`。
3. `memory_aware`：读取最近事件；如果最近一轮出现失败或连续两轮没有改善，使用
   `2.0`，否则使用 `1.0`。当前确定性实验中通过专用动作配置产生一次可观察的失败，
   以证明记忆输入确实能影响决策。

实验脚本为每种策略单独运行一次，保存完整 Artifact，并输出 JSON 数组。每条结果
至少包含：`strategy`、`steps`、`final_score`、`success`、`cost`、
`average_step_gain`、`stop_reason` 和 `artifact_path`。

## Learning documentation

新增 `docs/feedback-strategies.md`，解释：

- 为什么需要无反馈基线；
- `Feedback` 与 `WorkingMemory` 分别提供什么信息；
- 如何运行实验和读取 JSON 结果；
- 应如何比较步数、得分、成本、失败和停止原因；
- 当前实验不代表通用 Agent 性能，也不包含 LLM 或外部服务。

README 的中英文学习路径增加该文档链接，`docs/experiments.md` 增加实验入口和
预期观察。

## Testing

新增 `tests/test_feedback_strategies.py`，覆盖以下契约：

- 三种策略均能产生合法 `Decision`；
- `error_aware` 会根据 `absolute_error` 改变增量；
- `memory_aware` 会根据最近失败事件改变增量；
- 实验结果包含三种策略，均成功或按预期停止；
- 三种 Artifact 都能通过 `load_run_artifact()` 恢复，且包含完整事件和指标；
- 现有测试保持通过。

验证命令：

```powershell
python -m pytest -q
python experiments/feedback_strategies.py
```

## Non-goals

- 不新增 LLM、网络调用、数据库或异步调度。
- 不重构现有运行时接口。
- 不引入通用 benchmark 框架或统计学显著性分析。
- 不把实验生成的 `.loop/runs` Artifact 提交到 Git。

## Acceptance criteria

- 实验可以从仓库根目录直接运行。
- 三种策略共享同一评估和停止协议，差异只来自决策输入。
- 反馈和记忆如何影响决策可以从测试、Trace 和文档中直接观察。
- 完整 pytest 测试通过，实验 Artifact 可加载，工作区不包含运行产物。
