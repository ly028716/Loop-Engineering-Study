# 受控本地工具适配层

本项目的本地工具适配层用于学习：如何把一次可观察的、受控的诊断命令接入既有
Loop。它不是通用命令执行器，也不会默认执行任何工具。

## 明确注册，而非动态命令

每个工具在构造 `LocalToolAdapter` 时以 `ToolDefinition` 显式注册：

```python
ToolDefinition(
    name="python-version",
    executable=str(Path(sys.executable).resolve()),
    arguments=("--version",),
    working_directory=str(output_dir.resolve()),
    timeout_seconds=2.0,
)
```

可执行文件和工作目录必须都是绝对路径，且工作目录已经存在。名称不可为空且不可
重复；超时和输出上限必须为正数。适配器只运行定义中已有的 argv：

```python
subprocess.run(
    [definition.executable, *definition.arguments],
    cwd=definition.working_directory,
    shell=False,
    capture_output=True,
    text=True,
    timeout=definition.timeout_seconds,
    check=False,
)
```

因此，策略不能把任何参数拼进命令。`ToolAction` 只接受名称已注册且
`Decision.parameters == {}` 的决策；非空参数和未知工具名称都会抛出
`ToolAdapterError`。

## 循环中的可观察结果

一次执行产生 `ToolExecution`：成功标记、退出码、stdout、stderr 与耗时。stdout
和 stderr 分别最多保留 1000 个字符（或调用方指定的正数上限）。非零退出码与
超时不是运行时异常：它们会映射为 `ActionResult(success=False, cost=耗时)`，继续
由既有评估器、反馈和停止条件观察。

为保持已有 Artifact 契约稳定，`ACT` 事件仍然只有：

```json
{"success": true, "cost": 0.01}
```

工具输出不会进入 Trace 或 Artifact。教学实验会把受限输出放入独立的
`report.json`，以便观察命令结果，同时避免将任意诊断文本当作循环证据持久化。

## 运行教学实验

```powershell
python experiments/local_tool_adapter.py
```

该脚本仅注册当前 Python 解释器的固定 `--version` 命令。它不会访问网络，也不会
修改项目文件；它只在 `.loop/runs/local-tool-adapter/` 写入实验自己的
`artifact.json` 和 `report.json`。正常 CLI 与其他实验不会隐式注册或执行工具。

## 本阶段不支持的能力

- 任意 Shell 命令或 `shell=True`；
- 动态参数、动态 argv 或环境变量注入；
- 修改项目文件的工具；
- 网络工具、工具链或批量编排；
- 通过 CLI 隐式执行工具。

若要研究更多类型的工具，应先设计新的、同样显式且可测试的安全边界，而不是扩大
本适配层的输入接口。
