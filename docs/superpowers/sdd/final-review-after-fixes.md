# Loop Engineering Study 修复后最终复审

复审日期：2026-07-20  
工作区：`E:\IDEWorkplaces\VS\Loop-Engineering-Study`  
复审模式：只读检查；除本报告外未修改工作区文件，未提交，未修改 `.git`。  
依据：

- `docs/superpowers/plans/2026-07-20-loop-engineering-study.md`
- `docs/superpowers/sdd/final-review.md`
- `docs/superpowers/sdd/final-fix-report.md`

## 1. Verdict

**总 verdict：NOT READY**

**代码、构建、运行时与最终验收 A-1..A-8：READY。**

修复后的代码已经解决原审查 I-1 和 I-2：clean wheel 可构建，两个顶层包可从
wheel 隔离安装和导入；CLI 与三个直接实验都生成包含
`events`、`final_state`、`metrics` 的完整 UTF-8 artifact，loader round-trip
通过；完整测试、CLI smoke、三个直接实验和占位扫描均通过。

总 verdict 仍为 `NOT READY` 的唯一阻断项是计划 Global Constraint G-10：
当前 `.git` 是空目录，不是有效 Git 仓库，无法核验或满足 Task 1–8 的阶段独立
提交要求。这是交付环境/仓库元数据限制，不是当前 Python 实现缺陷；本轮按要求
没有尝试初始化、删除、重建或以其他方式破坏性修复 `.git`。

问题计数：

- Critical：0
- Important：1（I-3，交付环境限制）
- Minor：3（M-3、M-4、M-5）

## 2. Findings

### Critical

无。

### Important

#### [I-3] 空 `.git` 仍使阶段提交全局约束不可满足

位置：工作区 `.git/`

本轮实际结果：

```text
git status --short --branch
fatal: not a git repository (or any of the parent directories): .git
GIT_STATUS_EXIT=128

git rev-parse --is-inside-work-tree
fatal: not a git repository (or any of the parent directories): .git
GIT_REV_PARSE_EXIT=128

GIT_ENTRY_COUNT=0
```

影响：

- 无法取得 branch、HEAD、SHA、status 或 diff；
- 无法核验计划要求的 Task 1–8 每阶段独立小提交；
- 无法证明当前文件相对任何可信版本基线的变更边界；
- Global Constraint G-10 失败，因此总 verdict 不能是 `READY`。

该问题标记为**交付环境/仓库元数据限制**。代码与 A-1..A-8 验收不受影响，
但计划的全局版本控制约束未满足。

### Minor

#### [M-3] `LoopRunner` 的 memory 跨 `run()` 生命周期语义仍未形成明确契约

位置：`loop_engineering/runner.py:37,39-44,104-105`

同一 runner 实例被复用时，`run()` 不清空 `WorkingMemory`。本轮行为探针得到：

```text
FIRST_RUN_EVENTS=6
SECOND_TRACE_EVENTS=6
SECOND_DECIDE_CONTEXT_EVENTS=7
CROSS_RUN_MEMORY_RETAINED=True
SECOND_ARTIFACT_WOULD_OMIT_PRIOR_CONTEXT=True
```

第二次运行第一次决策可读取第一次运行的 6 个事件及第二次运行的 `OBSERVE`，
但第二次运行的 trace/artifact 不包含第一次运行的上下文。如果策略依赖该上下文，
仅凭第二个 artifact 不能完整解释或回放决策。当前 CLI 和三个实验每次都创建新
runner，因此不影响本轮验收。

#### [M-4] 已知文档表述偏差仍存在

位置：

- `docs/experiments.md:12-13`
- `docs/superpowers/sdd/task-4-report.md:26-28`
- `docs/superpowers/sdd/task-7-report.md:7`

`docs/experiments.md` 和 Task 7 报告仍使用 “bundled Python”，但仓库没有捆绑
解释器；Task 4 报告仍把停止原因描述为 final state 内容，并把 `STOPPED`
描述成事件，实际实现是 phase 为 `STOP`，其 payload 包含
`status="STOPPED"` 和 `reason`。这些不影响实现，但会降低学习材料和历史报告
的准确性。

#### [M-5] README 的 artifact 检查说明未显式点名完整 `metrics` 节点

位置：

- `README.md:57-63`
- `README.zh-CN.md:50-53`

双语 README 已说明如何运行命令、查看 JSON、读取 stdout 的 `score`，也说明
artifact 包含事件和最终状态；但未明确告诉学习者同一 artifact 顶层还有
`metrics`，以及其中的五个字段。`docs/concepts.md` 已正确说明该契约，因此这是
非阻塞的学习体验缺口。

## 3. 原 Important 修复复核

### I-1：显式包发现与安装面

**已修复。**

`pyproject.toml` 当前包含：

```toml
[tool.setuptools.packages.find]
include = ["loop_engineering*", "experiments*"]
```

从不含 `.git`、`.loop`、缓存、`build`、`dist`、egg-info 和 pyc 的全新临时
源码副本执行标准 PEP 517 隔离构建：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe `
  -m pip wheel `
  C:\Users\Administrator\AppData\Local\Temp\loop-engineering-after-fixes-aac90fc8e41a47c6afa128d5e54662da\source `
  --no-deps `
  --wheel-dir C:\Users\Administrator\AppData\Local\Temp\loop-engineering-after-fixes-aac90fc8e41a47c6afa128d5e54662da\dist
```

结果：

```text
Successfully built loop-engineering-study
WHEEL_BUILD_EXIT=0
filename=loop_engineering_study-0.1.0-py3-none-any.whl
WHEEL_SIZE=15530
WHEEL_SHA256=2e047489f78ede7b7a875e4a49113aa7228b774c4665ca5409a4c953bb2202ff
WHEEL_MEMBERS=22
WHEEL_REQUIRED_PRESENT=True
PACKAGES=experiments,loop_engineering
```

随后创建全新 venv，仅从本地 wheel 无依赖、无索引安装：

```text
VENV_CREATE_EXIT=0
Successfully installed loop-engineering-study-0.1.0
WHEEL_INSTALL_EXIT=0
```

隔离目录中以 `-I` 导入，实际来源均为 venv `site-packages`：

```text
INSTALLED_VERSION=0.1.0
LOOP_PACKAGE=...\venv\Lib\site-packages\loop_engineering\__init__.py
EXPERIMENTS_PACKAGE=...\venv\Lib\site-packages\experiments\__init__.py
INSTALLED_IMPORT_EXIT=0
```

模块 CLI 和 `loop-engineering` console script 均实际运行成功：

```text
{"status": "SUCCEEDED", "steps": 2, "final_value": 2.0, "score": 1.0, ...}
INSTALLED_MODULE_CLI_EXIT=0
INSTALLED_ENTRY_CLI_EXIT=0
INSTALLED_LOADER_STATUS=SUCCEEDED
INSTALLED_LOADER_EVENTS=11
INSTALLED_LOADER_METRICS=MetricReport(steps=2, final_score=1.0,
  success=True, cost=2.0, average_step_gain=0.5)
INSTALLED_LOADER_EXIT=0
```

### I-2：完整 UTF-8 run artifact 契约

**已修复。**

直接调用 `loop_engineering.artifacts.save_run_artifact()` 和
`load_run_artifact()`，使用包含中文事件、停止原因和 metadata 的对象完成探针：

```text
ARTIFACT_TOP_KEYS=events,final_state,metrics
METRIC_KEYS=average_step_gain,cost,final_score,steps,success
UTF8_TEXT_PRESENT=True
TRACE_ROUNDTRIP=True
METRICS_ROUNDTRIP=True
ARTIFACT_PROBE_EXIT=0
```

定向自动化测试：

```text
python -B -m pytest \
  tests/test_artifacts.py::test_run_artifact_round_trip_restores_trace_and_metrics -q

.                                                                        [100%]
1 passed in 0.78s
ARTIFACT_TEST_EXIT=0
```

## 4. 实际运行验证

所有会生成缓存、wheel、venv 或 run artifact 的命令都在以下临时验证根目录
执行，未写入工作区：

```text
C:\Users\Administrator\AppData\Local\Temp\
loop-engineering-after-fixes-aac90fc8e41a47c6afa128d5e54662da
```

验证解释器：

```text
Python 3.11.9
pip 26.1.2
```

### 4.1 完整测试

在临时源码副本运行：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe `
  -B -m pytest -q
```

结果：

```text
.........................................                                [100%]
41 passed in 3.89s
FULL_PYTEST_EXIT=0
```

### 4.2 CLI smoke

```powershell
python -B -m loop_engineering.cli run `
  --goal 3 `
  --max-steps 10 `
  --output <temp>\run-probes\cli-smoke.json
```

结果：

```json
{"status": "SUCCEEDED", "steps": 3, "final_value": 3.0, "score": 1.0, "trace_path": "<temp>\\run-probes\\cli-smoke.json"}
```

```text
CLI_SMOKE_EXIT=0
cli-smoke.json: exists=True events=16 status=SUCCEEDED
  keys_ok=True metric_keys_ok=True metrics_match=True stop=STOP
```

### 4.3 三个直接实验

实际运行：

```powershell
python -B experiments\basic_loop.py
python -B experiments\retry_loop.py
python -B experiments\repair_loop.py
```

关键输出：

```text
basic_loop:
steps=3
status=SUCCEEDED
score=1.0
artifact_path=<temp>\source\.loop\runs\basic_loop.json

retry_loop:
steps=3
status=SUCCEEDED
score=1.0
artifact_path=<temp>\source\.loop\runs\retry_loop.json

repair_loop:
steps=1
status=STOPPED
score=0.0
artifact_path=<temp>\source\.loop\runs\repair_loop.json
```

退出码和逐个 loader 复核：

```text
BASIC_DIRECT_EXIT=0
RETRY_DIRECT_EXIT=0
REPAIR_DIRECT_EXIT=0

basic_loop.json: exists=True events=16 status=SUCCEEDED
  keys_ok=True metric_keys_ok=True metrics_match=True stop=STOP
retry_loop.json: exists=True events=16 status=SUCCEEDED
  keys_ok=True metric_keys_ok=True metrics_match=True stop=STOP
repair_loop.json: exists=True events=6 status=STOPPED
  keys_ok=True metric_keys_ok=True metrics_match=True stop=STOP
RUN_ARTIFACT_LOADER_EXIT=0
```

普通包导入不再改变 `sys.path`：

```text
PACKAGE_IMPORT_PATH_UNCHANGED=True
```

### 4.4 占位扫描

扫描 README、公开 docs、theory、experiments、loop_engineering、tests 和 examples；
排除计划与 SDD 审查报告，因为这些文档会引用待办/占位词本身：

```powershell
rg -n -i `
  'TODO|TBD|FIXME|XXX|待补充|占位|placeholder|NotImplementedError' `
  README.md README.zh-CN.md docs theory experiments loop_engineering tests examples `
  -g '!docs/superpowers/plans/**' `
  -g '!docs/superpowers/sdd/**'
```

结果无输出：

```text
PLACEHOLDER_RG_EXIT=1
```

`rg` 退出码 `1` 表示没有匹配项。

### 4.5 本地 Markdown 链接

对双语 README、公开 docs、theory 和 examples 的相对 Markdown 链接进行路径解析：

```text
LOCAL_LINKS_CHECKED=44
BROKEN_LINKS=0
```

## 5. Global Constraints 覆盖

| ID | 要求 | 结果 | 本轮证据 |
| --- | --- | --- | --- |
| G-1 | 固定工作区 | PASS | 静态审查从指定工作区执行；运行产物放在临时副本。 |
| G-2 | 独立 Loop Engineering 项目 | PASS | README、docs、theory 和实验均围绕循环、反馈、记忆、收敛与停止。 |
| G-3 | 固定五阶段顺序 | PASS | `runner.py` 固定记录五阶段；CLI/实验 artifact 实测符合。 |
| G-4 | 每轮结构化 trace | PASS | 四个 run artifact 均可加载，事件数和最终 `STOP` 均通过。 |
| G-5 | deterministic、无外部服务 | PASS | 三个直接实验和 CLI 在无 API Key 环境实际运行。 |
| G-6 | 运行时只用标准库 | PASS | `dependencies = []`；pytest 仅在 dev extra；wheel 无运行时依赖安装。 |
| G-7 | 状态、事件、指标以 UTF-8 落盘 | PASS | UTF-8 中文探针与四个完整 artifact loader 检查通过。 |
| G-8 | 显式停止、无默认无限循环 | PASS | 成功、最大步数、安全上限均有测试；runner 使用有界 `range`。 |
| G-9 | 新组件有单测和实验 | PASS | 策略、动作、评估器、记忆和停止条件均有测试，并由三个实验覆盖。 |
| G-10 | 每阶段测试并独立小提交 | **FAIL** | 测试通过，但 `.git` 为空且 Git 命令退出 128，阶段提交无法核验或满足。 |

## 6. Task 1–8 覆盖

下表的 `PASS` 表示功能和验收内容通过；所有 Task 的 commit step 统一受 G-10
限制，不单独重复计入每行。

| Task | 结果 | 覆盖情况 |
| --- | --- | --- |
| Task 1：项目骨架与学习入口 | PASS | 版本、双语 README、六阶段学习路径、`.gitignore`、显式包发现、clean wheel 和隔离导入均通过。 |
| Task 2：领域模型与事件轨迹 | PASS | 模型、phase 校验、`LoopTrace`、UTF-8 JSONL round-trip 由完整测试覆盖。 |
| Task 3：策略、动作与评估器 | PASS | ABC 边界、确定性策略、未知动作拒绝、目标评估和 tolerance 测试均通过。 |
| Task 4：runner 与停止条件 | PASS | 五阶段顺序、跨轮反馈、成功/最大步数/安全上限和结构化 `STOP` 均通过。 |
| Task 5：记忆、指标与持久化 | PASS | 有界 memory、五字段 `MetricReport`、统一完整 artifact 保存/加载均通过；M-3 是非阻塞生命周期歧义。 |
| Task 6：CLI 与可回放输出 | PASS | 源码 CLI、安装后模块 CLI、console script、参数校验、stdout 摘要和 loader 均通过。 |
| Task 7：三个实验与理论文档 | PASS | 三个 `run() -> LoopTrace`、三个直接脚本、artifact_path、完整 artifact、不同教学语义和互链均通过。 |
| Task 8：项目级验证与学习体验 | PASS | 41 项测试、CLI smoke、占位扫描和 44 个本地链接均通过；M-5 是非阻塞说明缺口。 |

## 7. 最终验收 A-1..A-8

| ID | 验收标准 | 结果 | 证据 |
| --- | --- | --- | --- |
| A-1 | 无外部 API 运行完整确定性循环 | PASS | CLI 与三个实验均本地实际运行。 |
| A-2 | 每轮看到五阶段结构化事件 | PASS | CLI/实验 artifact loader 检查和 runner 测试通过。 |
| A-3 | 因成功、最大步数或显式条件停止 | PASS | `SUCCEEDED`、`STOPPED` 与 safety limit 测试覆盖。 |
| A-4 | trace、最终状态和指标落盘并重新读取 | PASS | UTF-8 round-trip、固定顶层键、五字段 metrics 与四个 loader 检查通过。 |
| A-5 | 策略、动作、评估器、记忆、停止条件可替换和测试 | PASS | 各组件独立测试及实验组合通过。 |
| A-6 | 至少三个实验展示不同问题 | PASS | basic、retry、repair 均直接运行且语义不同。 |
| A-7 | 理论文档与实验互链 | PASS | 44 个本地 Markdown 链接检查，0 断链。 |
| A-8 | 完整 pytest 和 CLI smoke 通过 | PASS | `41 passed`，CLI exit 0。 |

## 8. 最终结论

修复后的 Python 项目、wheel、隔离安装、CLI、三个直接实验、artifact 契约、
完整测试和 A-1..A-8 均达到 `READY`。

但实现计划明确包含“每个阶段独立小提交”的全局约束；当前空 `.git` 使该约束
既不能核验也不能满足。因此，在不放宽计划全局约束、且不修改 Git 元数据的前提下，
本次最终总 verdict 必须是：

**NOT READY**
