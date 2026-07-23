# Loop Engineering Study

> 一个可执行的 Loop Engineering 学习实验室。

Loop Engineering Study 是一个独立、本地优先的 Python 学习项目，用于研究
如何设计和评估可观察、可重复的改进循环。它是学习运行时和实验集合，不是
Agent 平台，也不是生产 Harness。

项目基线完全确定性运行，不需要 API Key、数据库、模型服务或 Web 框架。每次
运行都会显式呈现以下循环：

```text
OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK → STOP
```

## 当前已实现

- 具备明确状态、策略、动作、评估器、记忆、指标和停止条件边界的
  `LoopRunner`。
- 记录每一轮循环的结构化事件 Trace。
- 持久化包含 `events`、`final_state` 和 `metrics` 的 JSON Artifact。
- 可确定性复现的成功、重试、失败和停止行为。
- CLI，以及 `basic_loop`、`retry_loop`、`repair_loop` 三个可执行实验。
- 覆盖运行时和打包契约的 pytest 测试集。

项目刻意从确定性行为开始。外部模型或服务属于未来实验输入，不会成为当前
基线的隐式依赖。

## 快速开始

需要 Python 3.11 或更高版本：

```powershell
python -m pip install -e ".[dev]"
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json
Get-Content -Raw .loop/runs/demo.json
```

CLI 会输出 JSON 摘要，并写入一份可回放的完整 Artifact。按以下顺序运行三个
学习实验：

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
```

## 学习路径

建议先理解概念模型，再依次观察完整循环、反馈、记忆、收敛和停止行为：

1. [核心概念](docs/concepts.md)
2. [学习路径](docs/learning-path.md)
3. [实验说明](docs/experiments.md)
4. [反馈策略对比实验](docs/feedback-strategies.md)
5. [记忆容量对比实验](docs/memory-capacity.md)
6. [收敛与停止条件](docs/convergence-stopping.md)
7. [失败模式与恢复策略](docs/failure-modes.md)
8. [自适应策略与预算分配](docs/adaptive-strategy.md)
9. [评测基准与排行榜](docs/benchmark-suite.md)
10. [参数敏感性分析](docs/sensitivity-analysis.md)
11. [系统架构](docs/architecture.md)
12. [指标定义](docs/metrics.md)
13. [可回放 Artifact](docs/replay.md)
14. [理论笔记](theory/)

## 开发

```powershell
python -m pytest -q
python -m build --wheel
```

提交 Pull Request 前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。CI 会在支持的
Python 版本上执行相同的测试和 wheel 构建检查。

## 项目边界

本仓库是独立的 Loop Engineering 学习项目，不是通用自主 Agent 框架、LLM
编排系统或生产可靠性解决方案。新增能力应尽量保留可观察 Trace、可确定性
测试和显式停止条件。

## 许可证

项目采用 [MIT License](LICENSE) 发布。
