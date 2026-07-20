# Loop Examples

`experiments/` 中的模块是可运行案例；本目录保留为学习入口，方便从概念跳到
具体实验。

- `basic_loop` 用于理解稳定、限幅的目标逼近以及成功停止。
- `retry_loop` 用于理解将一次失败编码为反馈，并让下一轮决策据此改变。
- `repair_loop` 用于理解动作执行成功、底层状态达到目标和评估器判定成功是不同的
  事实。

从仓库根目录执行 `python -m experiments.basic_loop`（再依次运行其余两个）即可
开始。完整的运行顺序和输出说明见 [实验指南](../docs/experiments.md)。
