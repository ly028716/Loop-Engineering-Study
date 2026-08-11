# 进阶索引

在能够用本地 Artifact 解释一个闭环后，再选择下面一个方向扩展。每次引入外部能力时，都应保留显式边界、确定性替代路径和可诊断 trace。

- [外部 HTTP 模型适配层](../external-model-adapter.md)：以显式配置接入模型。
- [受控本地工具适配层](../local-tool-adapter.md)：以白名单执行本地诊断工具。
- [多目标评估](../multi-objective-evaluation.md) 与 [多修复方案选择](../multi-repair-selection.md)：比较多个候选改进。
- [随机性与鲁棒性](../stochastic-robustness.md)：在受控扰动下评估策略。
- [诊断驱动修复](../diagnosis-repair-loop.md) 与 [Trace 差异分析](../trace-diff-analysis.md)：把证据变成下一轮改动。
