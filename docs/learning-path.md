# Learning Path

本路径从概念逐步走向工程案例。所有基线实验均在本地确定性运行，不需要 API Key。
每一阶段都应保留可检查的 trace、指标或学习笔记。

## 开始之前

使用 Python 3.11 或更高版本，在项目根目录安装并运行第一个循环：

```powershell
python -m pip install -e ".[dev]"
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/learning.json
Get-Content -Raw .loop/runs/learning.json
```

POSIX shell 可将最后一条命令替换为 `cat .loop/runs/learning.json`。确认 JSON 摘要的
`status` 为 `SUCCEEDED`，并在 trace 中找到 `OBSERVE`、`DECIDE`、`ACT`、
`EVALUATE`、`FEEDBACK` 和最终的 `STOP`。

## 1. 概念

- 理解 Loop Engineering 的独立定位与核心循环。
- 区分观察、决策、行动、评估和反馈的职责。
- 练习把一个目标拆成当前状态、下一步动作和可验证结果。
- 阅读 [循环模型](../theory/loop-models.md)，将五阶段模型与 trace 事件对应起来。

## 2. 单轮循环

- 阅读并运行 [基础循环脚本](../experiments/basic_loop.py)，用确定性、无外部 API 的
  例子走完五个阶段。
- 为每个阶段记录输入、输出和最小可检查证据。
- 明确一轮循环的开始状态与结束状态。

## 3. 反馈

- 比较成功、部分成功和失败的评估结果。
- 说明反馈如何改变下一轮决策，而不是只作为日志。
- 识别反馈延迟、噪声和重复动作带来的风险。
- 阅读 [反馈系统](../theory/feedback-systems.md)，再运行
  [`experiments/retry_loop.py`](../experiments/retry_loop.py) 观察反馈如何改变动作。

## 4. 记忆

- 区分当前状态、短期工作记忆和可长期复用的经验。
- 规定记忆的容量、更新时机和读取范围。
- 练习用历史证据解释当前决策。
- 对照 [状态与记忆](../theory/state-and-memory.md) 检查 trace、状态和工作记忆的边界。

## 5. 收敛

- 观察目标距离、进展速度和重复失败。
- 设计明确的成功、最大步数和无进展停止条件。
- 验证循环在有限资源下不会无限运行。
- 结合 [收敛](../theory/convergence.md) 与
  [停止条件](../theory/stopping-conditions.md) 解释最终状态和 `STOP` 原因。

## 6. 工程案例

- 选择一个可重复的本地问题，定义目标、状态、动作和评估指标。
- 保存每轮 trace，支持回放、比较和定位偏差。
- 在没有外部 API 的环境中完成最小实验，再评估是否需要外部依赖。
- 阅读 [实验说明](experiments.md)，依次运行 `basic_loop.py`、`retry_loop.py` 和
  `repair_loop.py`，记录三个实验的状态、步数、分数和停止原因。
- 扩展时只替换策略、动作、评估器、记忆或停止条件中的一个，并保持现有 trace
  契约和测试可复现。
