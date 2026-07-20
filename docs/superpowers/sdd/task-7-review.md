# Task 7 审查报告

审查范围：`docs/superpowers/plans/2026-07-20-loop-engineering-study.md` 中的 Task 7 规格、`docs/superpowers/sdd/task-7-report.md`、三个实验模块、`tests/test_experiments.py`、五份 `theory/` 文档、`docs/experiments.md`、`examples/README.md`、相关 Task 1–6 运行时，以及完整测试套件。

## 1. 审查结论

- **Spec compliance：FAIL**
- **Code quality：CHANGES REQUIRED**
- **Document quality：PASS（有非阻塞建议）**
- **实验模块运行：PASS**
- **规格要求的脚本运行：FAIL**
- **完整回归：PASS，31 passed**
- **Task 8 准入：暂不允许**

Task 7 的主要实验逻辑成立：

- `basic_loop` 以 `0 → 2 → 4 → 5` 稳定逼近目标，得分为 `0.25 → 0.5 → 1.0`。
- `retry_loop` 首轮注入确定性失败，反馈中的 `retry_required=1.0` 使下一轮增量从 `1.0` 改为 `2.0`，最终成功停止。
- `repair_loop` 的 `ACT.success=true`，而故障评估器返回 `EVALUATE.success=false`，最终由最大步数停止，能够区分动作执行结果、底层状态和评估判定。
- 三个 `run()` 都返回 `LoopTrace`，trace 均以 `STOP` 结束。
- 实验只导入标准库语义和项目内部模块；`pyproject.toml` 的运行时依赖仍为空，没有网络或外部服务调用。

但 Task 7 的明确接口要求每个实验都能通过 `python experiments/<name>.py` 运行。实际执行三个命令均因 `ModuleNotFoundError: No module named 'loop_engineering'` 退出，退出码均为 1。报告和文档改用 `python -m experiments.<module>`，该方式可以运行，但不能替代规格指定的脚本入口。

因此，当前不能认定 Task 7 完成，也不允许进入 Task 8。应先修复三个直接脚本入口，并用 subprocess 测试覆盖规格命令和摘要输出，再复审准入。

## 2. 审查发现

### [必须修复] 三个实验不支持规格要求的直接脚本执行

规格证据：

- `docs/superpowers/plans/2026-07-20-loop-engineering-study.md:541` 要求 `python experiments/<name>.py`。
- 同一计划的 `:579` 明确把 `python experiments/basic_loop.py` 作为 smoke 命令。

实现证据：

- `experiments/basic_loop.py:5-11`
- `experiments/retry_loop.py:5-11`
- `experiments/repair_loop.py:5-11`

三个脚本都直接导入顶层包 `loop_engineering`。以文件路径启动时，Python 将 `experiments/` 作为首个模块搜索目录，项目根目录不在该入口的导入路径中，因此无法找到同级的 `loop_engineering/`。

独立复现结果：

```text
python experiments\basic_loop.py
ModuleNotFoundError: No module named 'loop_engineering'
basic_direct_exit=1

python experiments\retry_loop.py
ModuleNotFoundError: No module named 'loop_engineering'
retry_direct_exit=1

python experiments\repair_loop.py
ModuleNotFoundError: No module named 'loop_engineering'
repair_direct_exit=1
```

影响：

- “每个实验可独立执行”的公开合同未满足。
- Task 7 计划中的 basic smoke 未执行成功。
- 新用户照规格命令运行会在任何实验逻辑开始前失败。

建议修复方向：

1. 让三个脚本在从仓库根目录按文件路径启动时可以解析项目包。
2. 保留当前 `python -m experiments.<module>` 方式，避免修复直接入口时破坏模块入口。
3. 在 `tests/test_experiments.py` 中使用 `sys.executable` 和 subprocess 覆盖三个精确脚本命令，断言退出码为 0，并检查摘要字段。

### [建议修改] 实验测试只覆盖最小返回值合同，未覆盖各实验的关键教学语义

`tests/test_experiments.py:20-28` 当前只断言：

- 返回值是 `LoopTrace`；
- `final_state` 非空；
- 事件非空；
- 最后事件是 `STOP`。

这与计划给出的最小参数化测试一致，且三个模块均通过。不过，即使三个实验内部实现成完全相同的普通循环，这组测试仍会通过。它没有保护以下 Task 7 核心行为：

- `basic_loop` 的误差缩小、分数单调上升和成功停止；
- `retry_loop` 只失败一次，以及反馈确实把下一轮动作从 `1.0` 改为 `2.0`；
- `repair_loop` 的 `ACT.success=true`、`EVALUATE.success=false` 和最大步数停止；
- 三个可执行入口输出轮数、最终状态、最终分数、停止原因和得分序列。

建议在修复直接入口时一并补充这些断言。直接执行缺陷已经证明，当前测试通过不能代表完整实验合同通过。

### [仅供参考] 文档中的 “bundled Python” 表述不准确

`docs/experiments.md:12-13` 和 `task-7-report.md:7,33` 使用 “bundled Python” 表述，但当前项目没有随仓库提供 Python 解释器。实际验证使用的是机器上已有的 Python 3.11：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
```

建议改为“Python 3.11+ 解释器的完整路径”或“项目虚拟环境中的 Python”。这不会影响实验逻辑，但能避免读者误以为仓库自带解释器。

### [仅供参考] 报告的 basic smoke 是模块 smoke，不是计划规定的 smoke

`task-7-report.md:45` 执行的是：

```text
python -m experiments.basic_loop
```

该命令已独立复现成功，输出内容也与报告一致。但计划 `:579-581` 指定的是：

```text
python experiments/basic_loop.py
```

并给出 `status=SUCCEEDED`、`steps=`、`score=` 的预期片段。当前模块输出使用 `rounds:`、`final state: LoopState(... status='SUCCEEDED' ...)` 和 `final score:`。它在语义上包含要求的五类摘要，但不含计划列出的字面片段。

本项本身不作为额外阻塞项；真正的阻塞是计划规定的脚本命令退出码为 1。后续报告应明确区分“模块入口 smoke”与“规格脚本入口 smoke”。

## 3. Spec compliance

| 要求 | 结论 | 审查证据 |
| --- | --- | --- |
| `basic_loop.run() -> LoopTrace` | PASS | `experiments/basic_loop.py:14-23` 有明确返回注解并返回 runner trace；专项测试与手工 trace 检查通过。 |
| `retry_loop.run() -> LoopTrace` | PASS | `experiments/retry_loop.py:60-69` 有明确返回注解并返回 runner trace。 |
| `repair_loop.run() -> LoopTrace` | PASS | `experiments/repair_loop.py:26-35` 有明确返回注解并返回 runner trace。 |
| 三个 trace 最终为 `STOP` | PASS | `tests/test_experiments.py` 三个参数化用例通过；手工 trace 的最后事件也均为 `STOP`。 |
| 可通过 `python experiments/<name>.py` 独立执行 | **FAIL** | 三个命令均报 `ModuleNotFoundError`，退出码均为 1。 |
| 不调用外部服务 | PASS | 实验只导入项目内部模块；未发现网络、外部 API、凭据或 subprocess 调用；运行时依赖为空。 |
| deterministic | PASS | basic 使用固定步长；retry 每次 `run()` 都创建新的 `FailOnceAction` 并固定首轮失败；repair 使用固定故障评估器和一轮上限。多次调用没有外部状态依赖。 |
| basic 展示目标逼近 | PASS | 决策增量为 `2.0, 2.0, 1.0`，误差为 `3.0, 1.0, 0.0`，最终 `SUCCEEDED`。 |
| retry 注入一次失败 | PASS | 首个 `ACT.success=false`，之后两个 ACT 均成功。 |
| retry 反馈改变下一轮动作 | PASS | 首轮反馈包含 `retry_required=1.0`；DECIDE 增量从 `1.0` 变为 `2.0`。 |
| repair 区分动作成功与目标判定 | PASS | `ACT.success=true`，故障评估器返回 `EVALUATE.success=false`、score 0，最终状态为 `STOPPED`。文档同时说明底层数值已达到目标，明确区分三层事实。 |
| 输出轮数、最终状态、最终分数、停止原因、得分序列 | PARTIAL | 三个模块入口均输出五类信息；规格要求的脚本入口在打印摘要前失败。最终状态通过完整 `LoopState` 表示，status 嵌在对象文本中。 |
| 五份 theory 文档主题分工正确 | PASS | 分别覆盖 loop model、feedback、state/memory、convergence、stopping conditions。 |
| 五份 theory 文档链接实验 | PASS | 共检查 10 个 theory → experiment 相对链接，全部解析到现有文件。 |
| `docs/experiments.md` 给出学习顺序 | PASS | `docs/experiments.md:15-17` 按 basic → retry → repair 排列，并解释每步观察重点。 |
| `examples/README.md` 说明案例 | PASS | `examples/README.md:6-9` 分别说明三个案例，`:11-12` 链接实验指南。 |
| `tests/test_experiments.py` 覆盖三个 `run()` 最小合同 | PASS | 参数化覆盖三个模块，断言 `LoopTrace`、最终状态、事件和 `STOP`。 |
| 测试覆盖可执行入口与实验专属语义 | PARTIAL | 没有 subprocess 或实验专属断言；直接执行缺陷未被测试发现。 |
| 不提前实现 Task 8 | PASS（当前快照） | `tests/test_project_contract.py` 不存在，也没有 Task 8 报告；`docs/learning-path.md` 尚未加入 Task 8 要求的项目合同链接。 |

## 4. Code quality

### 优点

- 三个实验只负责组装 Task 3–5 的既有组件，没有把教学场景反向写入核心运行时。
- `FailOnceAction`、`RetryAwareEvaluator`、`FeedbackRetryPolicy` 和 `FaultyEvaluator` 的职责边界清楚，代码短且可读。
- retry 的因果链在 trace 中完整可见：失败动作 → 评估信号 → feedback → 新决策。
- repair 没有把动作执行成功直接等同于 loop 成功；停止状态来自显式 `MaxSteps(1)`。
- 每个 `run()` 都创建新的 runner 和场景对象，避免多个调用之间泄漏 `_has_failed` 状态。
- 所有实验都有显式停止条件，并受 `LoopRunner` 的 safety limit 保护。

### 需要改进

直接脚本入口与模块入口没有同时验证，导致最基本的可运行合同在完整套件全绿时仍然失败。根因不在核心 loop 逻辑，而在实验入口的 Python 导入上下文。修复应保持范围集中在 Task 7 实验入口及其合同测试，不需要修改 Task 1–6 的核心运行时。

三个 `main()` 中摘要生成代码完全重复，但当前规模很小，不建议为了消除少量重复而提前引入 Task 8 范围或公共 API。先修复可执行性和测试覆盖更重要。

## 5. Document quality 与链接质量

五份理论文档都采用“概念说明 → 当前运行时中的对应对象 → 实验链接”的结构，内容与实际代码基本一致：

- `loop-models.md` 解释阶段机、状态、策略、动作、评估和 trace，并链接 basic/repair。
- `feedback-systems.md` 解释反馈作为下一轮输入，并精确描述 retry 的信号和增量变化。
- `state-and-memory.md` 区分当前状态、完整 trace、有限工作记忆和反馈摘要，并链接 retry/basic。
- `convergence.md` 给出 basic 的真实数值与得分序列，并用 repair 说明单一评估指标可能失真。
- `stopping-conditions.md` 解释成功、最大步数和 safety stop，并链接全部三个实验。

链接检查结果：

- theory → experiment：10/10 存在；
- `docs/experiments.md` → theory：5/5 存在；
- `examples/README.md` → 实验指南：1/1 存在；
- 合计：16/16 相对链接有效。

文档中的运行顺序清楚，examples 入口简洁。主要问题是所有运行说明只展示 `python -m experiments.<module>`，避开了规格中的脚本命令，也掩盖了实际缺陷。修复后建议同时列出并验证两种入口，或至少把规格要求的文件路径入口作为首选命令。

另有两点轻微表述问题：

- `state-and-memory.md` 把 `LoopState` 称为“不可变快照”；它的 dataclass 是 frozen，但 `metadata` 字典仍可原地修改。更精确的说法是 `with_value()` 不修改原状态并返回新实例。
- `loop-models.md` 将 `STOP` 直接画在每轮五阶段之后；从实现看，`STOP` 只在停止条件命中或 safety limit 到达时出现。可改为条件分支表达，以免读者误解每轮都有 STOP。

这两项不阻塞 Task 7 准入，属于后续文档精度优化。

## 6. 实验可运行性与验证证据

验证解释器：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
```

### 完整测试套件

执行：

```text
python -m pytest -q
```

结果：

```text
...............................                                          [100%]
31 passed in 1.86s
```

报告声称 `31 passed in 1.82s`。通过数量完全一致，耗时差异属于正常波动，因此“全套 31 passed”可信。

### 实验专项测试

执行：

```text
python -m pytest tests\test_experiments.py -q
```

结果：

```text
...                                                                      [100%]
3 passed in 0.03s
```

### 模块入口 smoke

以下命令均成功：

```text
python -m experiments.basic_loop
python -m experiments.retry_loop
python -m experiments.repair_loop
```

关键摘要：

| 实验 | 轮数 | 最终状态 | 最终分数 | 停止原因 | 得分序列 |
| --- | ---: | --- | ---: | --- | --- |
| basic | 3 | `SUCCEEDED` | 1.0 | `Evaluation reported success` | `[0.25, 0.5, 1.0]` |
| retry | 3 | `SUCCEEDED` | 1.0 | `Evaluation reported success` | `[0.0, 0.5, 1.0]` |
| repair | 1 | `STOPPED` | 0.0 | `Reached maximum steps: 1` | `[0.0]` |

basic 模块 smoke 的输出与 `task-7-report.md` 逐项一致。因此报告中的 basic **模块** smoke 可信。

### 规格脚本入口 smoke

以下命令均失败：

```text
python experiments\basic_loop.py
python experiments\retry_loop.py
python experiments\repair_loop.py
```

共同错误：

```text
ModuleNotFoundError: No module named 'loop_engineering'
```

退出码均为 1。因此报告不能支持“Task 7 规格 smoke 成功”或“每个实验可按计划独立执行”的结论。

## 7. Task 8 边界

当前文件快照没有 `tests/test_project_contract.py`，也没有 Task 8 报告；未发现提前实现 Task 8 的专属测试或交付物。Task 7 的新增内容仍集中在 `experiments/`、`theory/`、实验指南、examples 说明和实验合同测试中。

工作区的 `.git` 是空目录，`git status` 和 `git log` 都返回 “not a git repository”。因此无法通过 diff 或提交历史精确证明 Task 7 相对 Task 6 的文件变更边界，也无法独立核验报告中的“未创建提交”。本次只能基于当前文件快照确认没有 Task 8 专属文件。

本次审查没有修改任何实现文件，也没有创建提交；只新增本审查报告。

## 8. Task 8 准入结论

**暂不允许进入 Task 8。**

进入 Task 8 前至少需要：

1. 修复三个 `python experiments/<name>.py` 入口，使其从仓库根目录执行时退出码为 0。
2. 为三个直接脚本入口增加 subprocess 回归测试。
3. 在测试中验证摘要至少包含轮数、最终状态、最终分数、停止原因和得分序列。
4. 重新运行 `tests/test_experiments.py`、三个规格 smoke 和完整测试套件。
5. 更新 Task 7 报告，明确记录规格命令，而不是只记录替代的 `-m` 模块命令。

完成以上阻塞项后，basic、retry、repair 的核心实验语义、理论文档和链接质量可以支持 Task 8；当前无需改动 Task 1–6 核心运行时。
