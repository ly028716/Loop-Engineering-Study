# Loop Models

本项目将一个可观察的控制循环表示为 `OBSERVE → DECIDE → ACT →
EVALUATE → FEEDBACK → STOP`。`LoopState` 保存当前数值、目标、轮数和
状态；`Policy` 根据状态与上一轮反馈产生 `Decision`；`Action` 把决策应用为
新的状态；`Evaluator` 对结果评分；停止条件决定何时产生最终 `STOP` 事件。

这种边界使“动作有没有执行”和“目标是否完成”成为两个可独立验证的判断：动作
返回 `ActionResult.success`，评估返回 `Evaluation.success`。完整运行返回
`LoopTrace`，其中包含所有阶段事件和最终状态。

从稳定的数值模型开始，请运行 [basic_loop](../experiments/basic_loop.py)。若要
观察评估与真实状态不一致的情况，请参阅 [repair_loop](../experiments/repair_loop.py)。
