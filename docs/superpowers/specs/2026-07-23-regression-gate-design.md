# Loop Engineering 回归门禁设计

## 目标

新增一个确定性回归门禁，将既有 benchmark、敏感性分析、Trace 诊断和诊断驱动修复闭环的关键能力固化为语义契约。门禁既可由 pytest 自动执行，也可作为独立 CLI 输出逐条证据。

门禁不修改运行时、策略、诊断器或 Artifact schema，不引入依赖，也不采用逐字 JSON 快照比较。

## 接口与报告

新增 `experiments/regression_gate.py`：

```python
def run_regression_gate(
    output_dir: str | Path = ".loop/runs/regression-gate",
) -> dict[str, object]:
    ...
```

返回 `{ "passed": bool, "checks": list[dict[str, object]] }`。检查按 `benchmark`、`sensitivity`、`diagnostics`、`repair_loop` 固定顺序输出；每条包含非空的 `name`、`passed` 与 `evidence`。四个子实验分别写入门禁目录下的独立子目录。

## 语义契约

| 检查 | 必须满足 |
| --- | --- |
| `benchmark` | 20 次运行、四种策略汇总，且 `adaptive.total_score > fixed.total_score`。 |
| `sensitivity` | 9 个配置、36 条运行记录；每个配置只改变声明参数；`goal_distance.no_flip=true`。 |
| `diagnostics` | 四个案例均完成；`action_failure`、`stalled_progress`、`budget_exhausted`、`recovery_observed` 全部出现；Artifact 和报告均存在。 |
| `repair_loop` | 三个案例均 `repair_succeeded=true`；修复摘要成功且不含目标诊断。 |

## 失败行为与验收

子实验抛出异常时 CLI 直接失败。实验成功运行但任何契约不满足时，CLI 输出完整的 `checks` 并以非零退出码结束。当前基线下 CLI 退出码为零且所有检查通过。

新增测试验证检查顺序、全通过状态、非空证据和门禁子目录产物；新增 `docs/regression-gate.md`，并更新实验导航、双语 README 与进度记录。完整 `pytest -q` 必须通过。

## 非目标

- 不保存或比较完整 JSON 快照；
- 不将门禁替代 benchmark 的完整评分解释；
- 不自动修复失败契约；
- 不配置外部 CI 服务或第三方通知。
