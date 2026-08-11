# 01：从失败的循环开始（10 分钟）

这一课面向已经会 Python、但想把 Agent 迭代闭环做成可诊断工程系统的开发者。你将从一个确定性的代码修复任务开始：候选修复 `off_by_one` 能让动作顺利执行，却仍不能通过边界测试。

## 运行基线

在项目根目录执行：

```powershell
python experiments/code_repair/baseline.py
```

脚本会把运行记录写入 `.loop/runs/code-repair/baseline.json`。它连续三次选择同一个候选修复，然后因为步数预算停止。

## 读懂第一条关键事实

终端中的 `Action succeeded` 只说明“执行候选修复”这个动作完成了；它不等于任务完成。随后评估器报告 `evaluation failed`：输入 `1` 的期望输出是 `1`，候选修复却给出了 `2`。

这正是 Loop Engineering 要解决的问题：把执行结果、评估信号和停止原因放在同一条可复查的 trace 中，而不是仅根据动作没有报错就宣布成功。

## 本课的闭环映射

| 闭环部件 | 这个案例中的职责 |
| --- | --- |
| Policy | 选择哪个候选修复 |
| Action | 将候选修复运行在测试输入上 |
| Evaluator | 比较实际输出与期望输出 |
| Stop policy | 成功、无进展或预算耗尽时停止 |
| Artifact | 保存完整 trace，供之后诊断与比较 |

下一课将用同一个问题，只改变一个部件，观察 trace 如何变化。
