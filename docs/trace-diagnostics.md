# Trace 诊断

Trace 诊断把一次已完成循环的事件序列转换为结构化、可复查的结论。它不修改循环本身，也不猜测不可观测的根因；每条诊断都给出支撑它的 Trace 事件索引。

## 运行实验

```powershell
python experiments/trace_diagnostics.py
```

脚本依次运行 `action_failure`、`stalled_progress`、`tight_budget` 和 `adaptive_recovery` 四个确定性案例。每个案例都会写入一份 Trace Artifact 和一份独立诊断报告：

- `.loop/runs/trace-diagnostics/<case>.artifact.json`
- `.loop/runs/trace-diagnostics/<case>.report.json`

Artifact 可使用 `loop_engineering.artifacts.load_run_artifact()` 回放；报告则用于直接比较诊断标签和证据。

## 四类诊断与证据

| 代码 | 严重级别 | Trace 证据 | 含义 |
| --- | --- | --- | --- |
| `action_failure` | `warning` | `ACT.success=false` | 一个或多个动作未成功执行。 |
| `stalled_progress` | `warning` | 成功 `ACT` 前后的 `OBSERVE.value` 没有变化 | 动作被报告成功，但没有推进状态值。 |
| `budget_exhausted` | `error` | 最大步数 `STOP` 且最终未成功 | 预算耗尽前未能完成目标。 |
| `recovery_observed` | `info` | 失败 `ACT` 后出现 `mode_code=3.0` 的 `DECIDE` | 自适应策略已发出恢复决策。 |

诊断器按表中顺序输出结果。停滞判断使用失败或成功动作前的 `OBSERVE.value`，再与下一个 `OBSERVE.value` 比较；最后一轮则与 `final_state.value` 比较。这样所有证据都来自已经持久化的 Trace。

## 阅读结构化报告

每一条 finding 都包含：

- `code`：稳定的诊断类别；
- `severity`：`info`、`warning` 或 `error`；
- `evidence_event_indices`：支撑结论的事件序号；
- `recommendation`：可在下一次实验中验证的固定改进方向。

例如，`adaptive_recovery` 同时包含 `action_failure` 与 `recovery_observed`：前者证明故障发生，后者定位故障之后的恢复决策。它不表示恢复一定成功，而是为比较恢复后的完成率与额外步数提供可回放证据。

## 解释边界

这些规则只分析当前项目保存的事件字段，适用于确定性学习实验。它们不使用 LLM，不执行实时监控，不自动修复策略，也不会修改既有 Artifact schema。诊断结论应被视为下一次 Loop Engineering 实验的可检验假设，而不是对真实服务故障的完整根因分析。
