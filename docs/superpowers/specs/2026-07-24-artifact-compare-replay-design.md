# Artifact 对比与回放工具设计

## 目标

为任意本地 Loop Artifact 提供通用命令行回放与对比能力。该能力复用既有 Artifact 持久化协议和 Trace 差异分析逻辑，不限于某个特定实验。

## 范围

新增两个 `loop_engineering.cli` 子命令，同时保持既有 `run` 命令和 Artifact JSON 格式不变：

```powershell
python -m loop_engineering.cli replay <artifact-path>
python -m loop_engineering.cli compare <left-artifact> <right-artifact>
```

不新增实验脚本、批量比较、HTML 可视化或新的 Artifact 存储格式。

## 命令契约

### `replay`

命令通过 `load_run_artifact()` 读取一个 Artifact，并打印 UTF-8 JSON：

```json
{
  "artifact_path": "<absolute path>",
  "events": ["<complete ordered events>"],
  "final_state": {"<final loop state>"},
  "metrics": {"<complete metric report>"}
}
```

`events` 必须包含完整、有序的事件记录；`final_state` 可为 `null`，以兼容领域模型允许的未终态 Trace。输出中的数据使用 `dataclasses.asdict()` 转成普通 JSON 值，`artifact_path` 使用解析后的绝对路径。

### `compare`

命令读取左右两个 Artifact，将恢复出的 Trace 与指标传给现有 `loop_engineering.trace_diff.compare_traces()`，并打印 UTF-8 JSON：

```json
{
  "left_artifact_path": "<absolute path>",
  "right_artifact_path": "<absolute path>",
  "identical": false,
  "difference": {"<first difference or null>"}
}
```

`difference` 使用 `TraceComparison` 的既有首分歧语义：按事件索引（步骤、阶段、payload）、事件数量、最终状态、指标的顺序报告；两个 Artifact 完全一致时为 `null`。该命令不引入第二套比较规则。

## 架构

`cli.py` 仅负责解析参数、读取文件、调用领域函数和序列化输出：

```text
CLI replay  -> load_run_artifact -> asdict -> JSON stdout
CLI compare -> load_run_artifact -> compare_traces -> asdict -> JSON stdout
```

Artifact 的校验、恢复和错误语义仍属于 `artifacts.py`；递归 Trace 比较仍属于纯模块 `trace_diff.py`。这使 CLI 命令可面向任何符合现有协议的 Artifact，同时不扩大领域模型的职责。

## 错误处理

CLI 不吞没缺失路径、无效 JSON 或不兼容 Artifact 所触发的异常；它们继续由 `load_run_artifact()` 以明确错误暴露。参数缺失仍由 `argparse` 处理。成功路径只输出 JSON 到标准输出。

## 测试与文档

新增 CLI 集成测试：

1. `replay` 对一个已保存 Artifact 输出完整事件、最终状态和指标，并使用绝对路径。
2. `compare` 对同一 Artifact 输出 `identical: true` 和 `difference: null`。
3. `compare` 对两个不同 Artifact 输出稳定的首分歧。
4. 既有 `run` 命令回归测试继续通过。

更新 `docs/replay.md`、`docs/experiments.md`、两份 README 学习路径以及进度记录，说明这两个通用命令、输出边界和与既有 Trace 差异实验的关系。

## 验收标准

- 任意由 `save_run_artifact()` 写入的 Artifact 可由 `replay` 完整输出。
- 任意两份兼容 Artifact 可由 `compare` 得到确定性的首分歧或一致结论。
- 未修改 Artifact 数据格式、既有 `run` 命令契约或 `trace_diff.py` 的比较语义。
- 完整 pytest 套件通过。
