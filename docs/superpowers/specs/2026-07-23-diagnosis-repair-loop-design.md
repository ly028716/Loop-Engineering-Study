# Loop Engineering 诊断驱动修复闭环设计

## 目标

新增一个确定性学习实验，将现有 Trace 诊断结果映射为明确的 Runner 配置修复，并通过真实重跑验证修复是否消除了目标诊断且完成任务。

本阶段关注透明的 Diagnose → Repair → Verify 闭环；不在 `LoopRunner` 中加入在线修复，不修改既有 Artifact schema，不引入第三方依赖，也不宣称为通用自动修复系统。

## 案例与修复映射

实验固定包含三个案例，按以下顺序运行：

| 案例 | 基线构建 | 目标诊断 | 修复构建 | 修复成功条件 |
| --- | --- | --- | --- | --- |
| `action_failure` | 复用失败模式中的一次失败动作 | `action_failure` | 使用 `NumericAction`、`IncrementPolicy(step_size=1.0)`、`GoalEvaluator`、`SuccessReached` 和 `MaxSteps(4)`，目标值 `3.0` | 成功，且没有 `action_failure` |
| `stalled_progress` | 复用 benchmark 的 `stalled_progress` / `fixed` | `stalled_progress`、`budget_exhausted` | 复用 benchmark 的 `steady_progress` / `fixed` | 成功，且两种诊断均消失 |
| `tight_budget` | 复用 benchmark 的 `tight_budget` / `fixed` | `budget_exhausted` | 复用 benchmark 的 `steady_progress` / `fixed`，预算 `8` | 成功，且没有 `budget_exhausted` |

`adaptive_recovery` 保持为 Trace 诊断实验中的信息性案例，不进入修复矩阵；`recovery_observed` 不是需要消除的错误标签。

## 实验接口与产物

新增 `experiments/diagnosis_repair_loop.py`，导出：

```python
def run_repair_loop(
    output_dir: str | Path = ".loop/runs/diagnosis-repair-loop",
) -> list[dict[str, object]]:
    ...
```

每个返回记录至少包含：

- `case`；
- `target_diagnostic_codes`；
- `baseline` 与 `repaired` 摘要；
- `baseline_artifact_path` 与 `repaired_artifact_path`；
- `report_path`；
- `repair_succeeded`。

`baseline` 和 `repaired` 摘要至少包含 `success`、`diagnostic_codes` 与 `findings`。每个案例保存以下文件：

- `<case>.baseline.artifact.json`；
- `<case>.repaired.artifact.json`；
- `<case>.report.json`。

所有文件位于 `.loop/runs/diagnosis-repair-loop/`。报告使用 UTF-8 JSON，包含与返回记录一致的可序列化数据。

## 修复判定

`repair_succeeded` 仅在以下三个条件全部满足时为 `true`：

1. 基线诊断代码包含至少一个 `target_diagnostic_codes` 中的值；
2. 修复运行的最终状态为 `SUCCEEDED`；
3. 修复诊断代码与 `target_diagnostic_codes` 没有交集。

该判定只评价目标诊断的消除和任务完成，不以分数提升替代完成条件，也不要求消除无关的信息性诊断。

## 测试与文档

1. 集成测试运行三个案例，验证三个 `repair_succeeded` 均为 `true`、六份 Artifact 可由 `load_run_artifact()` 回放、三份 JSON 报告可加载。
2. 测试验证每个基线摘要包含目标诊断，修复摘要不包含目标诊断且成功。
3. 重复运行保持案例顺序与诊断代码顺序稳定。
4. 新增 `docs/diagnosis-repair-loop.md`，更新实验导航、双语 README 和进度记录。
5. 完整 `pytest -q` 必须通过。

## 非目标

- 不从自由文本或 LLM 推断修复方案；
- 不在循环执行中动态改写策略；
- 不自动搜索全部可能的修复组合；
- 不修改历史 Trace 或制造假想修复结果。
