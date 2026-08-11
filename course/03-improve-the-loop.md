# 03：做一次可验证的改进（15 分钟）

目标不是“让 Agent 看起来更聪明”，而是基于 trace 提出一个最小假设，并用 before / after 运行证据验证它。

## 假设

基线没有改进的原因不是 Action 无法运行，而是重复策略忽略了 Evaluator 的推荐候选。因此只替换 Policy，保留问题、Action、Evaluator 和成功标准不变。

## 生成 before 与 after 证据

如果还没有运行过第一课，先执行基线；然后运行反馈策略：

```powershell
python experiments/code_repair/baseline.py
python experiments/code_repair/feedback_strategy.py
python -m loop_engineering.cli compare .loop/runs/code-repair/baseline.json .loop/runs/code-repair/feedback_strategy.json
```

第一个 Artifact 是 before：三步后预算耗尽，仍有失败测试。第二个 Artifact 是 after：第二次决策采用评估反馈，所有测试通过并以成功原因停止。

## 将案例迁移到自己的 Agent

把这次改进抽象为四个步骤：

1. 固定一个可重复问题和明确成功标准。
2. 记录每步的 decision、action result、evaluation 和 stop reason。
3. 从 Artifact 中定位没有发生状态改变的部件。
4. 每次只改一个部件，再比较 before / after Artifact。

小型框架中的 `Policy`、`Action`、`Evaluator` 与 `StopPolicy` 是可复用边界；`examples/code_repair` 则是它们如何协作的最小可运行参考。完成这里后，可阅读现有的[架构说明](../docs/architecture.md)和[指标说明](../docs/metrics.md)。下一项改造会为这些材料补上参考与进阶索引。
