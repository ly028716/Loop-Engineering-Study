# Task 7 最终复审

复审日期：2026-07-20  
工作区：`E:\IDEWorkplaces\VS\Loop-Engineering-Study`  
审查模式：只读实现；仅新增本审查文档，不修改实现文件，不提交。

## 1. 最终结论

- **Spec compliance：PASS**
- **Code/document quality：PASS（有 1 项非阻塞建议和 2 项参考意见）**
- **Task 8 准入：允许**

此前阻塞的直接脚本导入问题已解除。使用项目修复报告指定的 Python 3.11.9，
三个 `experiments/<name>.py` 入口和三个 `python -m experiments.<name>` 入口
均以退出码 0 完成。三个直接入口均输出 `status=`、`steps=`、`score=`，
同时也输出 `stop_reason=` 和 `scores=`。

`tests/test_experiments.py` 已使用 `subprocess.run()`、`sys.executable` 和仓库
根目录作为 `cwd`，参数化覆盖三个直接脚本入口。Task 7 专项测试为
`6 passed`，完整测试为 `34 passed`。

三个实验仍分别展示稳定逼近、反馈驱动重试和错误评估；每个 trace 的最后事件均为
`STOP`。五份理论文档主题完整，并且理论、实验指南和案例入口中的 16 个本地链接
全部解析成功。实验没有网络或外部服务依赖。

## 2. 审查意见

### [建议修改] 普通包导入会产生一次冗余的 `sys.path` 变更

位置：

- `experiments/basic_loop.py:5-10`
- `experiments/retry_loop.py:5-10`
- `experiments/repair_loop.py:5-10`
- `experiments/_bootstrap.py:13-18`

三个实验无论采用直接脚本还是包导入，都会在模块导入阶段调用
`prepare_script_imports(__file__)`。从仓库根目录执行普通包导入时，
`sys.path` 可能用空字符串表示当前目录；bootstrap 未把它视为项目根目录，
因而又把同一目录的绝对路径插入第 0 位。

本轮探针结果：

```text
bootstrap_import_changed=False
experiment_import_changed=True
added=["E:\\IDEWorkplaces\\VS\\Loop-Engineering-Study"]
first_entry='E:\\IDEWorkplaces\\VS\\Loop-Engineering-Study'
```

这项变更对直接脚本入口是必要的，但对已能导入 `experiments` 包的普通导入不是
必要的。建议后续只在 `__package__` 为空的直接脚本分支调用
`prepare_script_imports()`。

该问题不阻塞 Task 8，理由如下：

- 新增路径与已经由空字符串表示的当前工作目录等价，没有扩大可导入目录范围；
- 变更只存在于当前 Python 进程，不写文件、不改环境变量、不启动子进程；
- 三个直接入口、三个模块入口、专项测试和完整测试均通过；
- `_bootstrap.py` 自身导入不改变 `sys.path`，变更来自实验模块的无条件调用。

### [仅供参考] 模块命令尚无 subprocess smoke 回归

`tests/test_experiments.py` 已覆盖三个直接脚本入口，并通过包导入覆盖三个 `run()`
合同。三个 `python -m experiments.<name>` 命令本轮也都人工复核为退出码 0，
但测试尚未把 `-m` 命令作为 subprocess smoke 固化。

这不是 Task 7 原始规格缺口，也不影响本次放行；若后续继续承诺两种 CLI 入口，
可考虑把入口形式一起参数化。

### [仅供参考] “bundled Python” 文案不准确

`docs/experiments.md:12` 和既有 Task 7 报告使用了 “bundled Python” 表述，
但仓库没有随附 Python 解释器。本机当前 `PATH` 中也没有 `python` 命令，
本轮实际使用的是系统已安装的 Python 3.11.9 完整路径。

建议后续改为“已安装的 Python 3.11+ 解释器完整路径”。这是文档精度问题，
不属于 Task 7 实现阻塞。

## 3. Spec compliance

| 要求 | 结果 | 证据 |
|---|---|---|
| 三个实验暴露 `run() -> LoopTrace` | PASS | 三个模块均有明确返回注解；专项合同测试的 3 个参数化用例通过。 |
| 三个 trace 最终进入 `STOP` | PASS | 专项测试断言最后事件；本轮语义探针也显示三个 `last_phase` 均为 `STOP`。 |
| `basic_loop.py` 展示稳定目标逼近 | PASS | 决策增量为 `[2.0, 2.0, 1.0]`，分数为 `[0.25, 0.5, 1.0]`，最终值为 `5.0`、状态为 `SUCCEEDED`。 |
| `retry_loop.py` 注入一次失败并由反馈改变下一轮动作 | PASS | 动作成功序列为 `[false, true, true]`，增量从 `1.0` 改为 `2.0`，随后为 `1.0`；最终成功。 |
| `repair_loop.py` 区分动作成功与目标评估成功 | PASS | 动作成功且最终值为 `1.0`，评估仍为失败、分数为 `0.0`，最终由 `MaxSteps(1)` 停止。 |
| 三个直接脚本可运行 | PASS | 三个文件路径入口均退出 0。 |
| 三个模块入口保持可运行 | PASS | 三个 `-m` 入口均退出 0。 |
| 摘要包含轮数、状态、分数、停止原因和分数序列 | PASS | 三个入口均打印 `steps/status/score/stop_reason/scores`。 |
| smoke 测试覆盖直接脚本入口 | PASS | `tests/test_experiments.py:36-53` 参数化运行三个脚本并断言退出码及 `status/steps/score`。 |
| 五份理论文档覆盖指定主题并链接实验 | PASS | 主题分别为模型、反馈、状态/记忆、收敛和停止条件；10/10 个 theory → experiment 链接有效。 |
| 实验指南链接全部理论文档 | PASS | 5/5 个 docs → theory 链接有效。 |
| 无外部服务依赖 | PASS | `pyproject.toml` 的运行时 `dependencies = []`；实验导入仅包含标准库和 `loop_engineering`；外部服务关键字扫描无匹配。 |
| 完整测试为 34 项通过 | PASS | 本轮完整执行结果为 `34 passed in 3.01s`。 |

## 4. 运行证据

当前 shell 没有可用的 `python` 命令：

```text
python : 无法将“python”项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

因此，本轮使用修复报告记录的等价解释器路径：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
Python 3.11.9
```

### 4.1 直接脚本入口

```text
experiments\basic_loop.py
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.25, 0.5, 1.0]
EXIT=0
```

```text
experiments\retry_loop.py
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.0, 0.5, 1.0]
EXIT=0
```

```text
experiments\repair_loop.py
steps=1
status=STOPPED
score=0.0
stop_reason=Reached maximum steps: 1
scores=[0.0]
EXIT=0
```

### 4.2 模块入口

以下命令输出与对应直接入口一致，退出码均为 0：

```text
python.exe -m experiments.basic_loop
python.exe -m experiments.retry_loop
python.exe -m experiments.repair_loop
```

### 4.3 专项与完整测试

为避免审查运行产生字节码或 pytest 缓存，本轮设置
`PYTHONDONTWRITEBYTECODE=1` 并使用 `-p no:cacheprovider`。这不改变被测逻辑。

```text
python.exe -m pytest tests\test_experiments.py -q -p no:cacheprovider
......                                                                   [100%]
6 passed in 0.30s
EXIT=0
```

```text
python.exe -m pytest -q -p no:cacheprovider
..................................                                       [100%]
34 passed in 3.01s
EXIT=0
```

## 5. Code/document quality

### Bootstrap

`experiments/_bootstrap.py` 共 33 行，只承担两个职责：

1. 在直接脚本模式下提供项目根目录导入路径；
2. 使用现有 `MetricReport` 统一打印摘要。

实现使用 `pathlib`、`sys` 和 `TYPE_CHECKING`，没有文件写入、网络调用、外部服务、
环境变量修改或后台进程。项目根目录已存在时不会重复插入相同的绝对路径。

除第 2 节记录的普通包导入冗余路径插入外，未发现不必要的业务副作用。该建议不影响
Task 7 的接口和运行结果。

### 实验语义

- `basic_loop` 使用限幅增量和成功/最大步数停止条件，行为稳定且确定。
- `retry_loop` 将首次动作失败编码为 `retry_required`，下一轮策略确实读取该信号
  并扩大增量，反馈不是仅用于日志。
- `repair_loop` 让真实状态达到目标，同时用故障评估器报告失败，最后由最大步数停止，
  清楚展示动作结果、真实状态和评估结论的区别。

### 文档与链接

本轮共解析 16 个本地 Markdown 链接：

- theory → experiment：10/10 有效；
- `docs/experiments.md` → theory：5/5 有效；
- `examples/README.md` → 实验指南：1/1 有效；
- 断链：0。

理论描述与本轮 trace 探针一致，没有发现与实现相反的行为说明。

## 6. Task 8 准入

**允许进入 Task 8。**

此前唯一阻塞项——直接运行 `experiments/<name>.py` 时无法导入
`loop_engineering`——已经通过共享 bootstrap 和直接入口 smoke 测试修复。
Task 7 的接口、三类实验语义、最终 `STOP`、指标摘要、理论文档链接、本地运行约束
及完整回归均有本轮独立证据支持。

进入 Task 8 前没有必须修改的 Task 7 实现项。第 2 节的 `sys.path` 冗余插入、
模块 subprocess 测试和 “bundled Python” 文案可作为后续非阻塞清理。
