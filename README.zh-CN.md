# Loop Engineering 学习项目

这是一个独立的 Loop Engineering 学习与实验项目，研究如何围绕明确目标，
设计可观察、可重复的改进循环。项目不依附 Agent 平台，也不承担生产系统职责。
当前基线完全在本地确定性运行，不需要 API Key、数据库、模型服务或 Web 框架。

## 核心循环

`OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK`

- **OBSERVE（观察）**：记录当前状态与可用事实。
- **DECIDE（决策）**：选择下一步范围明确的动作。
- **ACT（行动）**：执行该动作。
- **EVALUATE（评估）**：根据目标检查结果。
- **FEEDBACK（反馈）**：把评估结果转化为下一轮输入。

每次运行都会在成功或命中其他显式停止条件后写入 **STOP（停止）** 事件。

## 安装

使用 Python 3.11 或更高版本，在项目根目录安装项目与 pytest 开发依赖：

```powershell
python -m pip install -e ".[dev]"
```

无需设置环境变量或凭据。

## 运行第一个循环

CLI 从 `0` 开始，每轮最多向目标增加 `1`，并把完整的可回放 JSON trace 写入
`--output` 指定路径。标准输出是包含 `status`、`steps`、`final_value`、`score` 和
`trace_path` 的 JSON 摘要。输出目录不存在时会自动创建。

Windows PowerShell：

```powershell
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json
Get-Content .loop/runs/demo.json
```

POSIX shell：

```sh
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json
cat .loop/runs/demo.json
```

`--max-steps` 必须至少为 `1`；无效值会返回非零退出码并在标准错误中说明原因。
成功运行时，摘要中的 `status` 为 `SUCCEEDED`。trace 的 `events` 数组依次记录
每轮的 `OBSERVE`、`DECIDE`、`ACT`、`EVALUATE`、`FEEDBACK`，并以 `STOP` 事件
结束；同一文件还包含最终状态，无需重新运行即可检查全过程。

## 运行实验

三个直接脚本分别展示稳定循环、反馈驱动的重试，以及错误评估：

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
```

建议先阅读 [实验说明](docs/experiments.md)，再按顺序运行并对照输出。

## 学习顺序

请按“概念 → 单轮循环 → 反馈 → 记忆 → 收敛 → 工程案例”学习。详细任务见
[docs/learning-path.md](docs/learning-path.md)，本阶段已确定的术语见
[docs/concepts.md](docs/concepts.md)。

当前实现将策略、动作、评估器、记忆和停止条件彼此分离。下一阶段可在保持 trace
契约不变的前提下替换其中一个组件；只有在理解并测试确定性行为后，才考虑接入外部
模型。
