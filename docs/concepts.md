# 当前首版概念

本项目已经实现一套可运行、可停止、可回放的 Loop Engineering 首版模型。它以
确定性的本地数值循环说明核心概念，不依赖外部 API 或第三方运行时库。

## 独立定位

Loop Engineering 关注“如何通过一轮又一轮的观察、决策、行动和评估实现改进”。
它是本项目的学习主题，不等同于 Agent 平台、模型服务或生产级编排系统。

## 运行时模型与核心循环

[领域模型](../loop_engineering/models.py) 定义状态、反馈、事件和完整运行轨迹；
[循环执行器](../loop_engineering/runner.py) 按以下固定顺序执行每一轮：

1. **OBSERVE**：获取并描述当前状态。
2. **DECIDE**：基于当前状态确定下一步动作。
3. **ACT**：执行已确定的动作。
4. **EVALUATE**：将动作结果与目标或评价标准比较。
5. **FEEDBACK**：整理评估结果，供下一轮观察或决策使用。

这 5 个阶段形成闭环。每个阶段都会产生结构化事件；运行结束时再记录 `STOP`
事件和最终状态，因此一次运行可以完整检查和回放。

## 可替换组件

首版把循环中的职责拆成独立接口和实现：

- [策略](../loop_engineering/policies.py) 根据状态和反馈生成决策。
- [动作](../loop_engineering/actions.py) 执行决策并返回新状态、成功标记和成本。
- [评估器](../loop_engineering/evaluators.py) 对动作结果评分并生成反馈信号。
- [停止条件](../loop_engineering/stopping.py) 显式决定成功、最大步数等终止原因；
  runner 还提供安全步数上限，避免无限循环。
- [工作记忆](../loop_engineering/memory.py) 以有界窗口向策略提供最近事件。
- [指标](../loop_engineering/metrics.py) 从轨迹派生步数、最终分数、成功状态、成本和
  平均单步增益，不修改运行状态。

## 持久化与入口

[run artifact 接口](../loop_engineering/artifacts.py) 将 `events`、`final_state`
和完整 `metrics` 保存为 UTF-8 JSON，并能恢复 `LoopTrace` 与
`MetricReport`。[JSONL 事件存储](../loop_engineering/trace_store.py) 则适合逐条
追加和读取事件。

[CLI](../loop_engineering/cli.py) 提供确定性的 `run` 命令，输出兼容的 JSON
摘要，并通过共享 artifact 接口保存完整运行结果。

## 可运行实验

3 个直接实验展示不同的循环行为，并将结果写入 `.loop/runs/`：

- [basic_loop](../experiments/basic_loop.py)：稳定逼近并达到目标。
- [retry_loop](../experiments/retry_loop.py)：首次动作失败后利用反馈重试。
- [repair_loop](../experiments/repair_loop.py)：动作达到目标，但故障评估器拒绝结果。

## 确定性与外部依赖

首版运行时只使用 Python 标准库。相同输入会产生相同事件、最终状态、指标和
artifact 内容，便于学习、测试和比较循环行为。
