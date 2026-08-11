# 学习路径

本项目的主线不是先阅读抽象概念，而是先完成一个确定性的诊断与改进闭环。适合已会 Python，想理解 AI/Agent 如何在可观察证据中迭代的开发者。

## 第一阶段：45 分钟主线

按顺序完成课程；不要跳过基线 Artifact，因为后续比较需要它。

1. [从失败的循环开始](../course/01-baseline.md)：运行坏候选，确认动作成功不等于评估成功。
2. [用 trace 定位问题](../course/02-read-the-trace.md)：分别观察评估信号、反馈策略和无进展停止。
3. [做一次可验证的改进](../course/03-improve-the-loop.md)：比较 before / after Artifact，并把方法迁移到自己的问题。

## 第二阶段：复用小型框架

阅读 [`examples/code_repair`](../examples/code_repair)，然后为自己的任务实现一个 Policy、Action、Evaluator 和 Stop policy。保持一个固定问题、可重复测试和可比较 Artifact；每轮只替换一个部件。

## 第三阶段：按需要深入

- [参考索引](reference/index.md)：概念、架构、指标、trace、基础实验和理论。
- [进阶索引](advanced/index.md)：模型/工具边界、多目标选择、随机性与诊断修复。

基础运行不需要外部服务。只有在已能解释本地 trace 后，才建议引入模型或工具适配层。
