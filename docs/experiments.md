# Experiments

所有实验都在本地运行，只依赖项目代码和 Python 标准库。建议按以下顺序进行：

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
python experiments/feedback_strategies.py
python experiments/memory_capacity.py
python experiments/convergence_stopping.py
python experiments/failure_modes.py
python experiments/adaptive_strategy.py
python experiments/benchmark_suite.py
python experiments/sensitivity_analysis.py
python experiments/trace_diagnostics.py
```

## 基础实验

`basic_loop.py` 展示一个稳定的目标逼近循环：策略每轮增加固定值，直到达到目标。

## 重试实验

`retry_loop.py` 注入一次动作失败。评估器将失败转换为
`retry_required` 反馈，策略读取该反馈后选择更大的下一步动作。

## 修复实验

`repair_loop.py` 展示动作结果和评估报告不一致的情况：状态可能已经达到目标，
但评估器仍然报告失败。这个实验提醒我们不能只看最终值，必须同时检查评估器和
停止条件。

## 反馈策略对比

`feedback_strategies.py` 比较 `fixed`、`error_aware` 和 `memory_aware` 三种策略。
详细说明见 [feedback-strategies.md](feedback-strategies.md)。

## 记忆容量对比

`memory_capacity.py` 比较 `no_memory`、`short_memory`、`working_memory` 和
`long_window` 四种记忆窗口。详细说明见 [memory-capacity.md](memory-capacity.md)。

## 收敛与停止条件

`convergence_stopping.py` 比较收敛、停滞和振荡三种模式，观察
`SuccessReached`、`NoProgress` 和 `MaxSteps` 的不同职责。详细说明见
[convergence-stopping.md](convergence-stopping.md)。

## 失败模式与恢复

`failure_modes.py` 统一比较动作失败、评估器冲突、反馈缺失、振荡和安全上限五种
场景。详细说明见 [failure-modes.md](failure-modes.md)。

## 自适应策略与预算分配

`adaptive_strategy.py` 在同一确定性失败和安全预算下比较 `fixed`、`error_aware`、
`memory_aware` 与 `adaptive` 四种策略。详细说明见
[adaptive-strategy.md](adaptive-strategy.md)。

## 评测基准与排行榜

`benchmark_suite.py` 在 5 个确定性场景中比较 4 种策略，输出场景明细、评分汇总和稳定排序的排行榜。详细说明见 [benchmark-suite.md](benchmark-suite.md)。

## 参数敏感性分析

`sensitivity_analysis.py` 对目标距离、失败发生时机和步数预算执行单参数扫描，比较相邻档位上的策略相对顺序，并报告首次排名翻转。详细说明见 [sensitivity-analysis.md](sensitivity-analysis.md)。

## Trace 诊断

`trace_diagnostics.py` 从可回放 Trace 中识别动作失败、进展停滞、预算耗尽和恢复决策，并保存独立的结构化诊断报告。详细说明见 [trace-diagnostics.md](trace-diagnostics.md)。

每个脚本都会输出摘要，并将完整 Trace 写入 `.loop/runs/`。运行产物可以通过
`loop_engineering.artifacts.load_run_artifact()` 加载。
