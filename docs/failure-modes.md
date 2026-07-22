# Failure modes and recovery

这个实验把循环系统中常见的失败情况拆成可观察的场景，分别检查检测证据、恢复行为
和最终停止原因。重点不是模拟所有生产故障，而是建立一组确定性、可回放的学习基线。

## Failure matrix

| 模式 | 触发方式 | 主要检测证据 | 预期结果 |
| --- | --- | --- | --- |
| `action_failure` | 第一次 Action 失败并发出 `retry_required` | 失败 `ACT` 与恢复反馈 | 重试后成功 |
| `evaluator_disagreement` | Action 成功、状态达标但评估失败 | Action、状态、Evaluation 不一致 | 记录冲突并停止 |
| `missing_feedback` | Action 失败但 `signals` 为空 | 失败事件与空反馈 | 保守增量继续运行 |
| `oscillation` | 状态值交替升降 | 分数交替变化 | 达到最大步数停止 |
| `safety_limit` | Action 持续失败 | 连续失败事件 | 安全上限停止 |

## 运行

```powershell
python experiments/failure_modes.py
```

脚本输出五条 JSON 结果，并在 `.loop/runs/failure-modes/` 下保存完整 Artifact。
运行产物已被 `.gitignore` 忽略。

## 结果字段

- `failure_count`：失败 `ACT` 事件数量；
- `recovery_attempts`：第一次失败后继续产生的 `DECIDE` 数量；
- `evidence_conflicts`：最终状态达到目标但评估仍报告失败的次数；
- `stop_reason`：最终 `STOP` 事件的原因。

这些字段需要结合 Trace 一起阅读。例如，`evaluator_disagreement` 的最终得分不能
单独证明状态失败，必须同时检查 Action 成功、最终状态和 Evaluation 报告。

## 查看证据

```python
from loop_engineering.artifacts import load_run_artifact

trace, report = load_run_artifact(
    ".loop/runs/failure-modes/evaluator_disagreement.json"
)
failed_actions = [
    event for event in trace.events
    if event.phase == "ACT" and event.payload.get("success") is False
]
print(report.success, report.final_score, failed_actions)
print(trace.events[-1].payload["reason"])
```

工程上，失败检测、恢复策略和停止条件是三个不同职责：检测发现异常，恢复尝试改变
下一轮行为，停止条件决定是否继续消耗资源。这个实验不代表通用 Agent 或 LLM 的
可靠性，也不提供跨运行故障监控。
