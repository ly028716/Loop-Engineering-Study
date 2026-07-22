# Failure Modes and Recovery Design

## Goal

建立一个统一的失败模式对比实验，展示动作失败、评估器冲突、反馈缺失、振荡和安全
上限等情况如何被检测、恢复和停止。

## Scope

本阶段新增一个场景注册式实验、测试和学习文档。复用现有 `LoopRunner`、Action、
Evaluator、Policy、Stopping Condition 和 Artifact 能力，不修改核心运行时接口，
不接入 LLM、网络服务、数据库或异步调度。

## Failure mode matrix

实验入口为 `experiments/failure_modes.py`，统一运行以下五个场景：

| 场景 | 触发方式 | 检测证据 | 预期结果 |
| --- | --- | --- | --- |
| `action_failure` | 第一次 Action 失败并产生 `retry_required` | 失败的 `ACT` 与恢复反馈 | 重试后 `SUCCEEDED` |
| `evaluator_disagreement` | Action 成功、状态达标但评估失败 | Action、状态和 Evaluation 不一致 | `STOPPED`，记录证据冲突 |
| `missing_feedback` | Action 失败但 Evaluation signals 为空 | 失败事件与空反馈信号 | 保守重试后成功或按上限停止 |
| `oscillation` | 状态值往返变化 | 得分交替升降 | `MaxSteps` 停止 |
| `safety_limit` | Action 持续失败 | 连续失败事件 | 安全上限停止 |

所有场景使用独立 Runner 和 Artifact。场景配置负责提供 Policy、Action、Evaluator
和停止条件；结果分析只读取完成后的 Trace，不改变运行状态。

## Result contract

每个场景输出一个 JSON 记录，字段包括：

- `failure_mode`
- `status`
- `success`
- `steps`
- `final_score`
- `failure_count`
- `recovery_attempts`
- `evidence_conflicts`
- `stop_reason`
- `artifact_path`

字段定义：

- `failure_count`：Trace 中 `ACT.payload.success == false` 的数量；
- `recovery_attempts`：失败之后发生的后续 `DECIDE` 次数；
- `evidence_conflicts`：Action 成功、最终状态达到目标但 Evaluation 失败的次数；
- `stop_reason`：最终 `STOP` 事件中的明确原因。

## Learning documentation

新增 `docs/failure-modes.md`，说明每种失败模式的最小复现、检测证据、恢复策略、
预期停止方式和 Artifact 查看方法。同时更新 `docs/experiments.md`、中英文 README
和进度记录。

## Testing

新增 `tests/test_failure_modes.py`，覆盖：

- 五种场景均可运行并生成 Artifact；
- `action_failure` 能被反馈恢复；
- `evaluator_disagreement` 能检测证据冲突；
- `missing_feedback` 能识别空 signals；
- `oscillation` 和 `safety_limit` 的停止原因正确；
- 每个 Artifact 都能通过 `load_run_artifact()` 加载；
- 现有完整测试保持通过。

## Non-goals

- 不实现通用故障编排框架。
- 不引入跨运行故障记忆、网络重试或外部监控系统。
- 不修改现有 Artifact JSON 字段结构。
- 不将实验运行产物提交到 Git。

## Acceptance criteria

- 可从仓库根目录直接运行 `python experiments/failure_modes.py`。
- 五种失败模式在 Trace、结果字段和文档中可区分。
- 恢复成功、证据冲突和安全停止均有明确验证。
- 完整 pytest 测试通过，Artifact 运行目录被 `.gitignore` 忽略。
