# Stopping Conditions

停止是循环模型的一等事件，而不是调用方的隐式约定。每次评估后，runner 按顺序
检查停止条件；第一个命中的条件确定最终状态与 STOP 原因。即使没有条件命中，
runner 的安全轮数上限也会生成 STOP 事件。

`SuccessReached` 用评估的成功标志结束运行，`MaxSteps` 防止无限循环。每个
Task 7 实验都在 trace 的末尾记录 `STOP`：

- [basic_loop](../experiments/basic_loop.py) 由评估成功停止。
- [retry_loop](../experiments/retry_loop.py) 在恢复后由评估成功停止。
- [repair_loop](../experiments/repair_loop.py) 因错误评估未报告成功，改由一轮的
  最大步数停止。

因此，停止原因也属于实验结果的一部分，应与最终状态和分数一起报告。
