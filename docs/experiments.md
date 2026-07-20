# Experiments

这些实验完全在本地运行，只使用项目的标准库依赖和已有的 loop-engineering
组件。请从仓库根目录按以下顺序运行：

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
```

若环境没有将 Python 加入 `PATH`，请将 `python` 替换为 bundled Python 的完整
路径。每个命令都会打印轮数、最终状态、最终分数、停止原因、每轮得分序列，以及
绝对 `artifact_path`。3 个 artifact 分别写入 `.loop/runs/basic_loop.json`、
`.loop/runs/retry_loop.json` 和 `.loop/runs/repair_loop.json`，均可通过
`loop_engineering.artifacts.load_run_artifact()` 恢复轨迹与完整指标。

1. `basic_loop`：先建立正常、稳定的目标逼近基线。
2. `retry_loop`：再观察一次确定性动作失败如何通过反馈改变下一轮增量。
3. `repair_loop`：最后观察“动作成功/状态达到目标”与“评估报告成功”并不等价。

可结合 [模型](../theory/loop-models.md)、[反馈](../theory/feedback-systems.md)、
[状态与记忆](../theory/state-and-memory.md)、[收敛](../theory/convergence.md) 和
[停止条件](../theory/stopping-conditions.md) 阅读。
