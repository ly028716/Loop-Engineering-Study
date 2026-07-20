# Loop Engineering Study 最终全项目审查

审查日期：2026-07-20  
工作区：`E:\IDEWorkplaces\VS\Loop-Engineering-Study`  
审查模式：不修改实现文件，不提交；仅写入本报告，并生成用户指定的
`.loop/runs/final-review.json` smoke 产物。

## 结论摘要

**Final verdict：NOT READY**

核心运行时本身是稳定的：37 项测试全部通过；CLI smoke 成功；三个直接实验脚本
均退出 0；每个正常完成的迭代都严格记录
`OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK`，并以结构化 `STOP`
结束；显式停止条件和安全上限可以阻止无限循环。

项目仍有三项未满足的计划约束：

1. setuptools 无法构建当前项目，README 中的安装路径不可用；
2. 落盘产物没有持久化完整 `MetricReport`，三个直接实验不写任何可回放产物；
3. `.git` 目录为空，无法满足或核验“每阶段独立小提交”的全局约束。

前两项是发布与验收阻塞项；第三项是交付过程与可审计性缺口。

## 1. Requirements coverage matrix

### 1.1 Global Constraints

| ID | 要求 | 结果 | 证据与说明 |
| --- | --- | --- | --- |
| G-1 | 工作区固定为计划路径 | PASS | 本轮所有命令均从指定路径执行。 |
| G-2 | 独立讲解 Loop Engineering，不复刻 Harness | PASS | README、docs、theory 和 examples 均围绕状态、反馈、收敛、记忆和停止；排除计划与 SDD 报告后，Harness 复刻关键字扫描无匹配。 |
| G-3 | 核心循环固定为五阶段 | PASS | `loop_engineering/runner.py:48-73` 固定阶段顺序；测试和本轮三个实验语义探针均通过。 |
| G-4 | 每轮产生结构化 trace | PASS | 五阶段和 `STOP` 都通过 `LoopEvent`/`LoopTrace.append()` 记录；CLI 产物有 16 个结构化事件。 |
| G-5 | 实验支持 deterministic、无外部服务 | PASS | 三个实验使用固定策略、固定故障注入和本地组件；运行时依赖为空，实际运行无需 API Key。 |
| G-6 | 运行时只用标准库，pytest 仅为开发依赖 | PASS | `dependencies = []`，`pytest` 只在 `project.optional-dependencies.dev`；源码导入未发现第三方运行时包。 |
| G-7 | 状态、事件和指标落盘为 UTF-8 JSON/JSONL | **FAIL** | CLI JSON 只有 `events` 和 `final_state`；完整 `MetricReport` 未落盘。三个直接实验只打印摘要，不写实验工作目录。 |
| G-8 | 停止条件显式可配置，禁止默认无限循环 | PASS | `SuccessReached`、`MaxSteps` 可配置；runner 另有校验过的 `safety_max_steps` 和有界 `range`。 |
| G-9 | 新策略、动作、评估器有单测及可运行实验 | PASS | 内置适配器有独立单测，并由 basic/retry/repair 实验组合使用。 |
| G-10 | 每阶段测试并独立小提交 | **NOT VERIFIABLE / FAIL** | 测试记录存在且本轮全量复验通过；但 `.git` 是空目录，所有历史报告也记录未提交，无法核验或满足阶段提交要求。 |

### 1.2 Task 1–8

| Task | 结果 | 覆盖情况 |
| --- | --- | --- |
| Task 1：项目骨架与学习入口 | **PARTIAL** | 包版本、双语 README、六阶段学习路径、`.gitignore` 和元数据字段存在；但当前平铺布局含 `loop_engineering` 与 `experiments` 两个顶层包，pyproject 未配置显式发现，wheel 元数据生成失败。 |
| Task 2：领域模型与事件轨迹 | PASS | `LoopState`、`Feedback`、`LoopEvent`、`LoopTrace` 和 UTF-8 `JsonlTraceStore` 接口存在，非法 phase 与 JSONL round-trip 有测试。 |
| Task 3：策略、动作、评估器 | PASS | ABC 边界清晰；未知动作拒绝执行；目标误差和 tolerance 边界有测试。 |
| Task 4：runner 与停止条件 | PASS | 五阶段固定顺序、反馈跨轮传递、成功/最大步数/安全上限停止和结构化 `STOP` 都有自动化与本轮实测证据。 |
| Task 5：记忆、指标、实验持久化 | **PARTIAL** | 有界 `WorkingMemory` 和纯 trace 派生的 `MetricReport` 正确；但“实验持久化”没有覆盖完整指标，也没有覆盖三个实验脚本。 |
| Task 6：CLI 与可回放输出 | **PARTIAL** | 模块 CLI、参数校验、JSON 摘要、事件和最终状态写入均通过；但安装入口无法构建，持久化文件缺少 metrics，且没有项目级 JSON loader。 |
| Task 7：三个实验与理论文档 | PASS | 三个 `run() -> LoopTrace`、三个直接脚本入口、摘要字段、教学语义、理论主题和本地链接均通过；repair 按设计以 `STOPPED` 结束。 |
| Task 8：项目级验证与学习体验 | **PARTIAL** | 37 项测试、CLI、三个脚本、占位扫描、文档链接检查均通过；但新用户 README 的安装步骤会在 setuptools 包发现阶段失败，且全局落盘契约未完成。 |

### 1.3 最终验收标准

| ID | 验收标准 | 结果 |
| --- | --- | --- |
| A-1 | 无外部 API 运行完整确定性循环 | PASS |
| A-2 | 每轮看到五阶段结构化事件 | PASS |
| A-3 | 成功、最大步数或其他显式条件停止 | PASS |
| A-4 | trace、最终状态和指标落盘并重新读取 | **FAIL** |
| A-5 | 策略、动作、评估器、记忆、停止条件可替换和测试 | PASS |
| A-6 | 至少三个实验展示不同问题 | PASS |
| A-7 | 理论文档与实验互链 | PASS |
| A-8 | 完整 pytest 和 CLI smoke 通过 | PASS |

## 2. 实际命令与退出结果

### 2.1 Python 入口

原始 PATH 探测：

```powershell
python --version
python -m pytest --version
```

结果：退出码 `1`；当前 shell 无法解析 `python`。因此以下必跑命令使用同一台机器上
现有的 Python 3.11 绝对路径：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
Python 3.11.9
```

### 2.2 完整 pytest

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
```

结果：

```text
.....................................                                    [100%]
37 passed in 2.53s
EXIT=0
```

### 2.3 CLI smoke

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/final-review.json
```

结果：

```json
{"status": "SUCCEEDED", "steps": 3, "final_value": 3.0, "score": 1.0, "trace_path": "E:\\IDEWorkplaces\\VS\\Loop-Engineering-Study\\.loop\\runs\\final-review.json"}
```

退出码：`0`。

对落盘 JSON 的独立检查结果：

```text
TRACE_STATUS=SUCCEEDED
TRACE_EVENT_COUNT=16
TRACE_PHASES=OBSERVE,DECIDE,ACT,EVALUATE,FEEDBACK,STOP
TRACE_MISSING=
TRACE_JSON_CHECK_EXIT=0
```

### 2.4 三个直接实验脚本

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/basic_loop.py
```

```text
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.25, 0.5, 1.0]
EXIT=0
```

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/retry_loop.py
```

```text
steps=3
status=SUCCEEDED
score=1.0
stop_reason=Evaluation reported success
scores=[0.0, 0.5, 1.0]
EXIT=0
```

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe experiments/repair_loop.py
```

```text
steps=1
status=STOPPED
score=0.0
stop_reason=Reached maximum steps: 1
scores=[0.0]
EXIT=0
```

额外语义探针确认三个实验的每个迭代都按五阶段分组，最后事件均为 `STOP`：

```text
basic_loop phase_order_ok=True last=STOP status=SUCCEEDED
retry_loop phase_order_ok=True last=STOP status=SUCCEEDED
repair_loop phase_order_ok=True last=STOP status=STOPPED
SEMANTIC_REPLAY_EXIT=0
```

### 2.5 源码/文档占位扫描

排除 `docs/superpowers/plans/**` 和 `docs/superpowers/sdd/**`：

```powershell
rg -n -i 'TODO|TBD|FIXME|XXX|待补充|占位|placeholder|NotImplementedError' README.md README.zh-CN.md docs theory experiments loop_engineering tests examples -g '!docs/superpowers/plans/**' -g '!docs/superpowers/sdd/**'
```

结果：无输出，`rg` 退出码 `1`，表示没有匹配项。

独立 Harness 复刻风险扫描同样无匹配：

```powershell
rg -n -i 'harness[-_ ]engineering|harness-engineering-study|agent harness|Harness Engineering' README.md README.zh-CN.md docs theory experiments loop_engineering tests examples -g '!docs/superpowers/plans/**' -g '!docs/superpowers/sdd/**'
```

结果：无输出，`rg` 退出码 `1`。

### 2.6 文档链接

对 README、docs、examples 和 theory 的本地 Markdown 链接做相对路径解析：

```text
LOCAL_LINKS_CHECKED=30
BROKEN_LINKS=0
EXIT=0
```

### 2.7 pyproject 构建验证

为避免污染工作区，在系统临时目录复制 `pyproject.toml`、两个顶层包和 README，
执行无依赖、无 build isolation 的 wheel 构建：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pip wheel C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-review-b17a8ac09c9a4605a91ff66b05297732 --no-deps --no-build-isolation --wheel-dir C:\Users\Administrator\AppData\Local\Temp\loop-engineering-final-review-b17a8ac09c9a4605a91ff66b05297732\dist
```

结果：退出码 `1`。

```text
error: Multiple top-level packages discovered in a flat-layout:
['experiments', 'loop_engineering'].
WHEEL_BUILD_EXIT=1
```

## 3. 重点专项检查

### 核心循环与 STOP

通过。`LoopRunner.run()` 沿单一控制流记录五阶段，条件命中和 safety limit
都统一进入 `_stop()`，写入包含 `status` 和 `reason` 的 `STOP` payload。
成功、最大步数和安全上限都有测试。本轮 CLI 和三个实验均再次验证了结构化
`STOP`。

异常从策略、动作或评估器向外抛出时不会生成 `STOP`；计划没有定义异常终止 trace
契约，因此本轮不将其列为阻塞缺陷。如果未来承诺“任何退出都可回放”，需要新增
结构化错误终止语义。

### 显式停止与无限循环

通过。`MaxSteps` 和 runner safety limit 都拒绝小于 1 的配置；主循环使用
`range(self.safety_max_steps)`，不存在默认无限循环。CLI 也在写文件前拒绝
`--max-steps < 1`。

### trace、状态与指标回放

部分通过。CLI JSON 可以用标准 JSON 读取并重建 `LoopTrace`，本轮重建后得到：

```text
MetricReport(steps=3, final_score=1.0, success=True, cost=3.0,
average_step_gain=0.33333333333333337)
```

但原始 artifact 的顶层键只有：

```text
artifact_keys=['events', 'final_state']
```

这证明指标可以重新计算，但没有按 Global Constraint 的字面要求落盘；
`JsonlTraceStore` 也只恢复事件，不恢复最终状态或指标。

### 组件职责边界

总体通过。models、policy、action、evaluator、stop condition、memory、metrics、
trace store、runner 和 CLI 的依赖方向清楚，CLI 没有把持久化或参数解析反向注入
runner。实验专用失败动作和故障评估器也留在 `experiments/`。

剩余的边界风险是 `LoopRunner` 的 memory 属于 runner 实例且跨多次 `run()` 保留，
而单次 trace 不记录初始 memory 上下文。当前 CLI/实验每次创建新 runner，不影响
现有结果；若支持复用 runner，需要明确“跨 run 记忆”还是“单 run 隔离”。

### 文档独立性

通过。公开学习文档围绕 Loop Engineering 的五阶段模型、反馈、状态/记忆、收敛和
停止条件展开，未复刻 Harness 的领域对象或命令结构。30 个本地文档链接全部有效。

## 4. Findings

### Critical

无。

### Important

#### [I-1] pyproject 无法发现多个顶层包，项目不能构建或按 README 安装

位置：

- `pyproject.toml:1-18`
- `experiments/__init__.py:1`
- `README.md:22-29`
- `README.zh-CN.md:19-25`

`pyproject.toml` 依赖 setuptools 自动发现，但仓库同时有 `loop_engineering` 和
`experiments` 两个顶层包。临时副本 wheel 构建在 metadata 阶段稳定失败。
因此当前测试仅证明“从源码根目录导入”可用，不能证明包安装入口可用；这直接破坏
Task 1 的包结构和 Task 8 的新用户安装路径。

最小修复建议：

```toml
[tool.setuptools.packages.find]
include = ["loop_engineering*", "experiments*"]
```

也可以显式列出 packages，但应保留已公开的 `python -m experiments.<name>` 能力。
修复后至少增加一个 clean wheel build 或 editable-install smoke。

#### [I-2] Global persistence/replay contract 未完成

位置：

- `loop_engineering/cli.py:46-58,70-87`
- `loop_engineering/trace_store.py:26-33`
- `experiments/_bootstrap.py:21-33`
- 三个实验的 `main()`

CLI 先写入仅含 `events`/`final_state` 的 JSON，随后才计算 `MetricReport` 并把
精简摘要输出到 stdout。完整指标字段 `success`、`cost` 和
`average_step_gain` 没有落盘。三个直接实验只打印摘要，也没有把事件、最终状态和
指标写入实验工作目录。项目还没有用于恢复 CLI artifact 的统一 loader。

这违反 Global Constraint G-7 和最终验收 A-4，也是当前 `NOT READY` 的直接原因。

最小修复范围：

1. 定义单一 UTF-8 run artifact：`events`、`final_state`、`metrics`；
2. 增加经过测试的加载/round-trip 接口，恢复 `LoopTrace` 和 `MetricReport`；
3. CLI 与三个直接实验都通过共享 helper 写入 `.loop/runs/` 或显式输出路径；
4. 测试断言落盘字段、UTF-8、重新加载后的对象和指标完全一致。

#### [I-3] 空 `.git` 使阶段提交约束和变更审计不可满足

位置：工作区 `.git/`。

`.git` 目录存在但为空，`git status --short --branch` 退出 128/报
“not a git repository”。Task 1–8 的报告也持续记录没有提交。因此不能核验计划
要求的每阶段独立提交，也无法用 diff 证明当前实现相对各阶段的精确边界。

最小处理范围：优先恢复真实仓库元数据和历史；若历史不可恢复，应初始化有效仓库、
透明记录“阶段历史不可追溯”的例外，并建立当前已验证基线。不能伪造过去的阶段提交。

### Minor

#### [M-1] `docs/concepts.md` 仍停留在 Task 1 口径

`docs/concepts.md:3-4` 声称本阶段“不定义运行时模型、持久化格式、策略接口或命令行
行为”，与最终项目现状和 README 的“current vocabulary”描述冲突。建议改为只解释
当前已实现且稳定的首版概念，并链接对应模块/文档。

#### [M-2] 实验包导入会冗余修改 `sys.path`

三个实验在直接脚本和普通包导入时都会无条件调用
`prepare_script_imports(__file__)`。直接脚本需要该行为，但普通
`import experiments.basic_loop` 已有仓库根路径时仍可能插入等价绝对路径。
建议只在 `__package__` 为空的直接脚本分支执行 bootstrap。

#### [M-3] memory 跨 run 生命周期未形成明确契约

`LoopRunner` 构造时持有 memory，`run()` 不清空。自定义策略若依赖
`recent_events`，复用同一 runner 时会读取上一次 run 的事件，但本次 trace
不包含该初始上下文。建议明确并测试跨 run 共享或单 run 隔离；若共享，应把初始
memory 上下文纳入可回放 artifact。

#### [M-4] 历史报告有已知但未修正的表述偏差

`task-4-report.md` 曾把停止原因描述为 final state 字段、把 `STOPPED` 描述成 phase；
Task 4 review 已指出实际为 `STOP` payload。Task 7 部分文档/报告使用
“bundled Python”，但仓库并未捆绑解释器。它们不影响当前实现，但会降低报告作为
长期学习资料的精度。

## 5. 测试与回归风险判断

- 当前已覆盖的确定性正常路径回归风险低：37 项测试、CLI、三个直接实验均通过。
- 最大风险不在五阶段 runner，而在安装面和 artifact 契约；现有测试从源码根目录
  运行，无法发现 setuptools 包发现失败。
- 现有 CLI 测试把“可回放”限定为 JSON 可解析和阶段存在，未断言完整 metrics
  持久化，也未验证统一 loader。
- 三个实验的 subprocess 测试只检查 `status/steps/score` 文本，没有检查 artifact
  生成，因为当前实现没有该能力。

## 6. Final verdict 与最小修复范围

**NOT READY**

转为 `READY` 的最小范围：

1. 在 pyproject 中显式配置包发现，并通过 clean wheel/editable-install smoke；
2. 统一持久化 `events + final_state + metrics`，让 CLI 和三个实验都生成可加载的
   UTF-8 run artifact，并补 round-trip 测试；
3. 恢复有效 Git 仓库元数据，或透明记录无法恢复阶段历史的例外并建立当前基线；
4. 重新执行完整 pytest、用户指定 CLI、三个直接实验、占位扫描和 wheel 构建。

Minor 项不必阻塞上述最小修复后的再次验收，但建议同步清理文档口径与 memory
生命周期说明。
