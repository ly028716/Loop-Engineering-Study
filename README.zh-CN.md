# Loop Engineering Study

> 给已会 Python、想系统理解 AI/Agent 如何通过“决策—执行—评估—反馈”迭代改进的开发者。

这是一个**45 分钟、可本地运行的 Loop Engineering 课程**，同时附带一个小型可复用框架。你不需要 API Key、模型服务或网络：先从一个会失败的代码修复 Agent 开始，读懂 trace，再用证据完成一次改进。

## 你会学到什么

完成主线后，你能回答并用 Artifact 证明：

- 为什么循环没有改进：是 Policy 忽略了反馈、Evaluator 没有给出可行动信号，还是 Stop policy 只是在耗尽预算？
- 为什么“动作执行成功”不代表任务已经成功？
- 如何只改一个闭环部件，并比较改进前后的运行证据？

课程使用一个确定性的 Python 函数修复案例：第一个候选补丁在部分输入上可运行，但会在边界测试失败；第二个候选补丁才能通过全部测试。

## 45 分钟主线

先安装开发依赖（Python 3.11+）：

```powershell
python -m pip install -e ".[dev]"
```

然后按顺序完成三节课：

1. [从失败的循环开始](course/01-baseline.md)（10 分钟）——运行 [`experiments/code_repair/baseline.py`](experiments/code_repair/baseline.py)，区分 action 成功与 evaluation 成功。
2. [用 trace 定位“为什么没有改进”](course/02-read-the-trace.md)（20 分钟）——完成三个只改变一个部件的实验。
3. [做一次可验证的改进](course/03-improve-the-loop.md)（15 分钟）——比较 before / after Artifact，验证反馈驱动的 Policy 改动。

主线命令也可以直接从这里运行：

```powershell
python experiments/code_repair/baseline.py
python experiments/code_repair/evaluator_signal.py
python experiments/code_repair/feedback_strategy.py
python experiments/code_repair/stopping_policy.py
```

每次运行都会写入 `.loop/runs/code-repair/`，保存完整事件、最终状态、指标和停止原因。

## 小型框架如何对应课程

| 课程问题 | 可复用边界 | 代码位置 |
| --- | --- | --- |
| 下一步尝试什么 | `Policy` | `loop_engineering/policies.py` |
| 如何执行尝试 | `Action` | `loop_engineering/actions.py` |
| 是否真的变好 | `Evaluator` | `loop_engineering/evaluators.py` |
| 何时停止 | `StopPolicy` | `loop_engineering/stopping.py` |
| 如何保存和比较证据 | Artifact / CLI | `loop_engineering/artifacts.py` |

案例实现位于 [`examples/code_repair`](examples/code_repair)，你可以复制它的边界并替换自己的问题、动作和评估器。

## 继续学习

- [课程学习路径](docs/learning-path.md)：课程结束后的练习与迁移方式。
- [参考索引](docs/reference/index.md)：架构、指标、概念、实验与理论材料。
- [进阶索引](docs/advanced/index.md)：外部模型、受控工具、多目标评估和鲁棒性实验。

## 开发与验证

```powershell
python -m pytest -q
python scripts/check_docs.py
python -m build --wheel
```

提交变更前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；发布时使用[发布检查清单](docs/release-checklist.md)。项目采用 [MIT License](LICENSE)。
