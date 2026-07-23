# 诊断驱动修复闭环

本实验把可回放 Trace 的诊断结果映射为确定性的修复配置，并通过真实重跑验证修复是否有效。它展示的是 Diagnose → Repair → Verify 学习闭环，而不是通用自动修复系统。

## 运行实验

```powershell
python experiments/diagnosis_repair_loop.py
```

每个案例会保存基线与修复后的两份 Artifact，以及一份结构化报告：

- `.loop/runs/diagnosis-repair-loop/<case>.baseline.artifact.json`
- `.loop/runs/diagnosis-repair-loop/<case>.repaired.artifact.json`
- `.loop/runs/diagnosis-repair-loop/<case>.report.json`

三个案例共生成六份 Artifact 与三份报告。

## 三个修复映射

| 案例 | 基线诊断 | 修复 | 预期结果 |
| --- | --- | --- | --- |
| `action_failure` | `action_failure` | 用正常数值动作替换一次失败动作 | 成功完成且没有动作失败诊断 |
| `stalled_progress` | `stalled_progress`、`budget_exhausted` | 用正常推进动作替换停滞动作 | 成功完成且两类诊断均消失 |
| `tight_budget` | `budget_exhausted` | 将 3 步预算恢复为 8 步 | 成功完成且预算耗尽诊断消失 |

## 判定修复成功

报告中的 `repair_succeeded` 仅在三项条件同时满足时为 `true`：基线确实包含目标诊断、修复后 Trace 为 `SUCCEEDED`、修复后的诊断代码不再与目标诊断相交。

因此，单纯提高分数或改变 Trace 不足以证明修复成功；学习者可以使用两份 Artifact 回放修复前后的事件证据。

## 解释边界

修复映射是为这三个确定性案例预先声明的规则，不会在循环执行中动态改写策略，也不会搜索其他可能的修复组合。它用于学习如何验证一个诊断假设，而非对真实服务执行根因分析或自动修复。
