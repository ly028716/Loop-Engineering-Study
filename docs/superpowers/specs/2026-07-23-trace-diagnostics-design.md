# Loop Engineering Trace 诊断设计

## 目标

新增一个基于既有 `LoopTrace` 的确定性规则诊断层。学习者可以从 Trace 中获得动作失败、进展停滞、预算耗尽和恢复决策四类结构化结论，并定位支撑结论的事件证据。

诊断器只读取已完成的 Trace；不修改 `LoopRunner`、策略、停止条件或 Artifact JSON 格式，也不引入第三方依赖。

## 模块与接口

新增 `loop_engineering/diagnostics.py`，导出：

```python
@dataclass(frozen=True)
class DiagnosticFinding:
    code: str
    severity: str
    message: str
    evidence_event_indices: tuple[int, ...]
    recommendation: str


def diagnose_trace(
    trace: LoopTrace,
    step_budget: int | None = None,
) -> list[DiagnosticFinding]:
    ...
```

诊断结果按规则声明顺序稳定输出。`code` 仅能是 `action_failure`、`stalled_progress`、`budget_exhausted` 或 `recovery_observed`；`severity` 仅能是 `info`、`warning` 或 `error`。每个 finding 至少包含一个有效的 Trace 事件索引，建议文案为固定字符串，便于测试与比较。

## 规则与证据

| 代码 | 触发条件 | 严重级别 | 证据 | 建议 |
| --- | --- | --- | --- | --- |
| `action_failure` | 存在 `ACT` 事件且 `success=false` | `warning` | 所有失败 `ACT` 事件 | 检查反馈信号并选择恢复动作。 |
| `stalled_progress` | 成功 `ACT` 后的状态值与动作前相同 | `warning` | 无状态推进的成功 `ACT` 事件 | 检查动作语义、进展信号和停滞停止条件。 |
| `budget_exhausted` | `STOP.reason` 为最大步数且最终状态未成功 | `error` | 最终 `STOP` 事件 | 调整预算、动作幅度或提前终止策略。 |
| `recovery_observed` | 失败动作之后出现 `DECIDE.parameters.mode_code == 3.0` | `info` | 失败 `ACT` 与对应恢复 `DECIDE` 事件 | 比较恢复后的完成率和额外步数。 |

“状态值”使用某个 `ACT` 事件之前 `OBSERVE.payload.value` 与其后下一次 `OBSERVE.payload.value` 比较；若该动作位于 Trace 的最后一轮，则使用 `trace.final_state.value` 作为结果值。实现必须只使用当前 Trace 已持久化的数据。若某个 Trace 不触发规则，诊断器返回空列表而不是生成虚构的诊断结果。

## 实验与报告

新增 `experiments/trace_diagnostics.py`，运行四个确定性案例：

1. 动作失败：产生 `action_failure`。
2. 停滞进展：产生 `stalled_progress`，并在预算内未完成时同时产生 `budget_exhausted`。
3. 紧预算：在最大步数停止且未成功时产生 `budget_exhausted`。
4. 自适应恢复：失败后产生恢复模式决策，得到 `action_failure` 与 `recovery_observed`。

实验复用现有 Action、策略、评估器和 Artifact API。每个案例保存一份 Trace Artifact 与一份 JSON 诊断报告到 `.loop/runs/trace-diagnostics/`。报告至少包含 `case`、`artifact_path`、`step_budget` 与序列化后的 `findings`。

## 测试与验收

1. 单元测试覆盖四条规则，断言 finding 的 `code`、`severity`、固定建议与有效证据事件索引。
2. 集成测试运行四个案例，验证四类标签都出现，诊断报告可读取，所有 Artifact 可由 `load_run_artifact()` 回放。
3. 重复运行具有相同的代码顺序、严重级别和证据索引。
4. 新增 `docs/trace-diagnostics.md`，并更新 `docs/experiments.md`、`README.md`、`README.zh-CN.md` 与进度记录。
5. 完整 `pytest -q` 必须通过。

## 非目标

- 不使用 LLM 或文本生成进行根因推断。
- 不在循环运行期间执行实时诊断。
- 不自动修改策略或修复运行。
- 不改变既有 Artifact JSON schema。
