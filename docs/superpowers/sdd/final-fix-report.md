# Loop Engineering Study 最终修复报告

修复日期：2026-07-20  
工作区：`E:\IDEWorkplaces\VS\Loop-Engineering-Study`  
修复范围：I-1、I-2、M-1、M-2  
Git 操作：未执行 commit，未创建、伪造或修改 `.git` 元数据。

## 结果摘要

- I-1：`pyproject.toml` 已显式发现 `loop_engineering*` 与 `experiments*`。
  干净临时源码副本成功构建 wheel；wheel 同时包含两个顶层包，并在全新 venv
  中完成安装、导入、命令入口和 artifact loader smoke。
- I-2：新增共享 UTF-8 JSON artifact 保存/加载接口。顶层包含 `events`、
  `final_state`、`metrics`；`metrics` 完整包含 `steps`、`final_score`、
  `success`、`cost`、`average_step_gain`。CLI 保留原 stdout 摘要，3 个直接
  实验均写入明确的 `.loop/runs/*.json` 并打印 `artifact_path`。
- M-1：`docs/concepts.md` 已改为当前首版实现口径，并链接运行时模型、组件、
  artifact、CLI 与实验模块。
- M-2：实验 bootstrap 只在直接脚本分支调用；普通包导入不改变 `sys.path`。

## TDD 与根因证据

修复前基线：

```text
37 passed in 2.24s
```

修复前 clean wheel 复现：

```text
error: Multiple top-level packages discovered in a flat-layout:
['experiments', 'loop_engineering'].
WHEEL_EXIT=1
```

修复前 artifact 与导入探针：

```text
ARTIFACT_KEYS=['events', 'final_state']
METRICS_PRESENT=False
PATH_CHANGED=True
INSERTED=['E:\IDEWorkplaces\VS\Loop-Engineering-Study']
```

新增测试在实现前分别因以下预期原因失败：

- `ModuleNotFoundError: No module named 'loop_engineering.artifacts'`；
- setuptools 多顶层包自动发现失败；
- `docs/concepts.md` 仍包含“不定义运行时模型”旧口径。

实现后的相关定向测试：

```text
...............                                                          [100%]
15 passed in 2.84s
```

## 必跑验证

### 1. 完整 pytest

命令：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
```

最终结果：

```text
.........................................                                [100%]
41 passed in 3.20s
FINAL_PYTEST_EXIT=0
```

### 2. Clean wheel build 与安装 smoke

先把最新的 `pyproject.toml`、`README.md`、`loop_engineering/` 和
`experiments/` 复制到全新临时源码目录，再执行：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe `
  -m pip wheel `
  C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-fix-42024f6230b84fd08fb31bfb301065fe\source `
  --no-deps `
  --wheel-dir C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-fix-42024f6230b84fd08fb31bfb301065fe\dist
```

构建结果：

```text
Successfully built loop-engineering-study
filename=loop_engineering_study-0.1.0-py3-none-any.whl
size=15530
sha256=d08acc8c87b139d78293249772421b3f086f6e48142d1778f0d1ab6cbb485f1e
WHEEL_REQUIRED_PRESENT=True
WHEEL_MEMBERS=22
WHEEL_BUILD_EXIT=0
WHEEL_INSPECT_EXIT=0
```

wheel 内容检查明确包含：

```text
loop_engineering/__init__.py
loop_engineering/artifacts.py
experiments/__init__.py
experiments/basic_loop.py
```

随后创建全新 venv，并仅从本地 wheel 安装：

```powershell
C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-fix-42024f6230b84fd08fb31bfb301065fe\venv\Scripts\python.exe `
  -m pip install `
  C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-fix-42024f6230b84fd08fb31bfb301065fe\dist\loop_engineering_study-0.1.0-py3-none-any.whl `
  --no-deps `
  --no-index
```

安装态结果：

```text
Successfully installed loop-engineering-study-0.1.0
INSTALLED_VERSION=0.1.0
INSTALLED_PACKAGES=loop_engineering,experiments
INSTALLED_ARTIFACT_API=True
INSTALLED_CLI_STATUS=SUCCEEDED
INSTALLED_CLI_METRICS=MetricReport(steps=2, final_score=1.0, success=True,
cost=2.0, average_step_gain=0.5)
VENV_EXIT=0
WHEEL_INSTALL_EXIT=0
INSTALLED_IMPORT_EXIT=0
INSTALLED_ENTRY_EXIT=0
INSTALLED_LOADER_EXIT=0
```

说明：系统 Python 的全局环境只有 setuptools 65.5.0，且没有 `wheel` 模块，
所以 `--no-build-isolation` 会因缺少 `bdist_wheel` 失败。上述最终构建使用
pyproject 标准隔离构建，按 `[build-system]` 安装 `setuptools>=68` 后成功；
这不是运行时依赖。

### 3. CLI smoke

命令：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe `
  -m loop_engineering.cli run `
  --goal 3 `
  --max-steps 10 `
  --output .loop\runs\final-fix-cli.json
```

stdout 保持兼容：

```json
{"status": "SUCCEEDED", "steps": 3, "final_value": 3.0, "score": 1.0, "trace_path": "E:\\IDEWorkplaces\\VS\\Loop-Engineering-Study\\.loop\\runs\\final-fix-cli.json"}
```

共享 loader 检查：

```text
ARTIFACT_KEYS=events,final_state,metrics
METRIC_KEYS=average_step_gain,cost,final_score,steps,success
LOADED_STATUS=SUCCEEDED
LOADED_EVENTS=16
METRICS_MATCH_TRACE=True
CLI_EXIT=0
LOADER_EXIT=0
```

### 4. 三个直接实验

命令：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\basic_loop.py
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\retry_loop.py
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments\repair_loop.py
```

关键输出：

```text
basic_loop:
steps=3
status=SUCCEEDED
score=1.0
artifact_path=E:\IDEWorkplaces\VS\Loop-Engineering-Study\.loop\runs\basic_loop.json

retry_loop:
steps=3
status=SUCCEEDED
score=1.0
artifact_path=E:\IDEWorkplaces\VS\Loop-Engineering-Study\.loop\runs\retry_loop.json

repair_loop:
steps=1
status=STOPPED
score=0.0
artifact_path=E:\IDEWorkplaces\VS\Loop-Engineering-Study\.loop\runs\repair_loop.json
```

逐个 loader 检查：

```text
basic_loop.json: exists=True events=16 status=SUCCEEDED metrics_match=True
retry_loop.json: exists=True events=16 status=SUCCEEDED metrics_match=True
repair_loop.json: exists=True events=6 status=STOPPED metrics_match=True
BASIC_EXIT=0
RETRY_EXIT=0
REPAIR_EXIT=0
EXPERIMENT_LOADER_EXIT=0
```

### 5. Artifact loader round-trip

命令：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe `
  -m pytest `
  tests/test_artifacts.py::test_run_artifact_round_trip_restores_trace_and_metrics `
  -q
```

结果：

```text
.                                                                        [100%]
1 passed in 0.74s
```

该测试同时验证：

- UTF-8 中文内容按原文落盘；
- 顶层 `events`、`final_state`、`metrics` 存在；
- 5 个 `MetricReport` 字段和值完整；
- loader 恢复的 `LoopTrace` 和 `MetricReport` 与保存前对象相等。

### 6. 占位扫描

命令：

```powershell
rg -n -i 'TODO|TBD|FIXME|XXX|待补充|占位|placeholder|NotImplementedError' `
  README.md README.zh-CN.md docs theory experiments loop_engineering tests examples `
  -g '!docs/superpowers/plans/**' `
  -g '!docs/superpowers/sdd/**'
```

结果：

```text
PLACEHOLDER_MATCHES=0
RG_EXIT=1
```

`rg` 的退出码 `1` 表示没有匹配项。

### 7. M-2 独立导入探针

命令等价于：

```python
import sys

before = list(sys.path)
import experiments.basic_loop

print(sys.path == before)
```

结果：

```text
PACKAGE_IMPORT_PATH_UNCHANGED=True
IMPORT_PROBE_EXIT=0
```

## 生成的验收 artifact

- `.loop/runs/final-fix-cli.json`
- `.loop/runs/basic_loop.json`
- `.loop/runs/retry_loop.json`
- `.loop/runs/repair_loop.json`

## 剩余顾虑

1. 当前 `.git` 不是有效仓库，无法生成可靠 diff 或 SHA；按用户要求未修改其元数据，
   也未执行 commit。最终审查中的 I-3 仍属工作区外部状态问题。
2. `LoopRunner` 的 memory 跨多次 `run()` 生命周期语义（原审查 M-3）不在本次
   I-1/I-2/M-1/M-2 修复范围内，保持原状。
3. 实际 clean wheel 使用标准隔离构建来取得 pyproject 声明的构建工具；运行时
   `dependencies` 仍为空，三个实验和 CLI 无外部运行时依赖。
