# Convergence and stopping

收敛不是“运行了很多轮”，而是状态或评估结果持续朝目标改善。停止条件则把循环
何时结束变成显式、可观察、可测试的协议。

## `NoProgress`

`NoProgress(window=3, min_score_gain=0.0)` 读取最近的 `EVALUATE` 分数：

- 评估样本不足时继续运行；
- 如果最近窗口内每次相邻得分提升都不超过阈值，则停止；
- 返回 `STOPPED` 和 `No progress for 3 evaluations`；
- 不负责判断目标是否达成，成功判断仍由 `SuccessReached` 完成。

这与 `MaxSteps` 不同：`NoProgress` 是基于行为结果的停止，`MaxSteps` 是资源和
安全边界。一个循环可能没有进展但尚未达到最大步数，也可能不断振荡并产生变化，
因此不应该把两者混为一谈。

## 三种模式

| 模式 | 评估趋势 | 停止原因 |
| --- | --- | --- |
| `converging` | 分数持续提升直到达到目标 | `Evaluation reported success` |
| `stalled` | 分数连续不变 | `No progress for 3 evaluations` |
| `oscillating` | 分数升降交替 | `Reached maximum steps: 6` |

## 运行实验

```powershell
python experiments/convergence_stopping.py
```

脚本会输出三条 JSON 结果，并在 `.loop/runs/convergence-stopping/` 下保存完整
Artifact。运行产物已被 `.gitignore` 忽略。

## 检查收敛趋势

```python
from loop_engineering.artifacts import load_run_artifact

trace, report = load_run_artifact(
    ".loop/runs/convergence-stopping/oscillating.json"
)
scores = [
    event.payload["score"]
    for event in trace.events
    if event.phase == "EVALUATE"
]
print(report.steps, report.success, scores)
print(trace.events[-1].payload["reason"])
```

观察 `score_history` 和最后的 `STOP` 事件，可以区分成功收敛、持续停滞和振荡耗尽
步数。这些实验是确定性的 Loop Engineering 教学案例，不代表通用 Agent 或 LLM
的收敛性能。
