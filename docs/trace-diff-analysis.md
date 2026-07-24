# Trace 差异分析

Trace 差异分析以同一案例的基线与修复后 Artifact 为输入，按事件顺序定位第一个可观察分歧，并保留两次运行的最终状态和指标摘要。它用于解释修复从哪里开始改变 Loop 行为，而不是重新执行或修改既有运行。

## 运行实验

```powershell
python experiments/trace_diff_analysis.py
```

实验依次比较 `action_failure`、`stalled_progress` 和 `tight_budget` 三组诊断修复案例。汇总报告写入 `.loop/runs/trace-diff-analysis/report.json`；每组案例的两份 Artifact 位于同一输出目录的 `repair-loop/` 子目录。

## 如何阅读首分歧

`comparison.first_difference` 是按事件索引顺序找到的第一个不同点：

- `event`：同一事件位置的 `step`、`phase` 或 `payload` 字段不同。
- `event_count`：公共事件前缀相同，但某一侧出现了缺失或新增事件。
- `final_state`：事件完全相同，最终状态不同。
- `metrics`：事件和最终状态完全相同，但派生指标不同。

分歧记录包含事件索引、阶段、字段路径，以及基线与修复后的值。后续事件常由这一处变化连锁产生，因此报告刻意不枚举所有后续差异。

## 报告结构

每个记录包含案例名、两份 Artifact 路径、既有 `repair_succeeded` 结论和 `comparison`。`comparison` 同时保留两侧事件数量、最终状态快照和指标快照，方便将首分歧与最终学习结果一起阅读。

## 解释边界

首分歧是运行行为发生变化的起点，不是自动根因判断。比较器不执行 Action、不重放外部副作用，也不使用编辑距离对不同控制流进行重新匹配。它只对已持久化的证据进行确定性的只读比较。
