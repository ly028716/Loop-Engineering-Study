# 02：用 trace 定位“为什么没有改进”（20 分钟）

本课的规则是：一次只改一个闭环部件。运行下面三个实验，并比较终端摘要和 `.loop/runs/code-repair/` 下的 Artifact。

## 实验 A：评估器与动作不是一回事（5 分钟）

```powershell
python experiments/code_repair/evaluator_signal.py
```

动作可成功执行，但测试仍失败。这证明 trace 必须同时保留 action 状态和 evaluator 信号；只记录异常或返回值，无法解释任务是否真的完成。

## 实验 B：让 Policy 使用反馈（8 分钟）

```powershell
python experiments/code_repair/feedback_strategy.py
```

与基线相比，Action 和 Evaluator 都没有改动。区别仅在 Policy：它读取评估器给出的 `recommended_candidate`，第二步从 `off_by_one` 切换到 `fix_boundary`，最终通过全部测试。

## 实验 C：没有进展就停止（7 分钟）

```powershell
python experiments/code_repair/stopping_policy.py
```

此实验仍重复同一个坏候选，但 Stop policy 增加了无进展检测，因此不会盲目耗尽五步预算。它回答的是不同问题：即使不会改进，循环如何以可解释的原因及时停止？

## 诊断清单

面对任一 Agent trace，依次问：

1. 每一步 Policy 根据了哪些状态和信号做决策？
2. Action 是否真正执行完成，还是只是不报错？
3. Evaluator 的失败信号是否足以指出下一步需要改变什么？
4. 停止是成功、无进展还是预算耗尽？

下一课把这个清单用于一次最小改进，并用前后 Artifact 验证效果。
