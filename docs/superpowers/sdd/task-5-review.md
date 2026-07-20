# Task 5 审查报告

审查范围：`docs/superpowers/plans/2026-07-20-loop-engineering-study.md` 中的 Task 5 规格、`docs/superpowers/sdd/task-5-report.md`、`loop_engineering/memory.py`、`loop_engineering/metrics.py`、`loop_engineering/runner.py`、相关模型与策略接口、`tests/test_memory.py`、`tests/test_metrics.py`、`tests/test_runner.py`、完整测试套件及当前工作区文件清单。

## 1. 审查结论

- **Spec compliance：PASS**
- **Code quality：APPROVED**
- **回归风险：LOW**
- **Task 6 准入：允许**

未发现必须修复的问题。`WorkingMemory`、`MetricReport.from_trace` 和 runner 的 memory 集成都符合 Task 5 要求；Task 4 的阶段顺序、停止行为、反馈传递和既有两参数策略调用保持兼容。Task 5 定向测试与完整测试已在当前环境中独立复现，分别为 `9 passed` 和 `26 passed`。

## 2. 审查发现

### [建议修改] 非修改性测试使用浅快照，不能发现 payload 的原地修改

`tests/test_metrics.py:30-31` 通过 `list(trace.events)` 和 `trace.final_state` 身份保存调用前状态。列表副本仍引用同一批 `LoopEvent`，`LoopState.metadata` 和 `LoopEvent.payload` 也都是可变字典；如果未来实现原地修改这些字典，`trace.events == original_events` 仍可能通过。

当前 `MetricReport.from_trace` 只构造局部列表、读取 payload、执行数值转换和求和，没有任何写操作，因此这不是当前实现缺陷，也不阻塞 Task 6。建议后续把调用前事件序列化，或使用 `copy.deepcopy()` 保存快照，再比较调用前后内容。

### [仅供参考] 明确 runner 复用时 memory 的生命周期

`loop_engineering/runner.py:37` 将 memory 保存为 runner 实例状态，`run()` 开始时不会清空。因此，同一个 `LoopRunner` 连续执行多次时，后一轮运行的策略可以看到前一次运行留下的最近事件；当前运行返回的 `LoopTrace` 则只包含本次事件。

该行为仍满足有界状态要求，也没有违反 Task 5 的明确规格。对于 Task 6 的单次 CLI 运行不会产生影响。建议在后续实验设计中明确 memory 是「单次 run 隔离」还是「runner 生命周期内共享」；如果选择共享，应确保回放产物同时保存影响决策的初始 memory 上下文。

除此之外，未发现必须修复、建议修改或仅供参考级别的实现问题。

## 3. Spec compliance：PASS

| 要求 | 结论 | 审查证据 |
| --- | --- | --- |
| `WorkingMemory` 使用 `deque(maxlen=capacity)` | PASS | `memory.py:5,17` 直接使用 `collections.deque(maxlen=capacity)`，满容量后由 deque 自动淘汰最旧事件。 |
| `capacity < 1` 明确失败 | PASS | `memory.py:13-15` 在构造时抛出带 `capacity` 信息的 `ValueError`；`test_memory.py:32-36` 覆盖 `capacity=0`。同一分支也覆盖所有负值。 |
| `add()` 行为正确 | PASS | `memory.py:19-22` 以插入顺序追加事件；`test_memory.py:10-18` 验证容量为 2 时只保留步骤 2、3。 |
| `recent()` 行为正确 | PASS | `memory.py:24-29` 返回最多 `limit` 条最新事件，并保持时间顺序；非正 limit 返回空列表。`test_memory.py:21-29` 覆盖尾部查询和零 limit。 |
| `MetricReport` 字段完整且不可变 | PASS | `metrics.py:10-18` 使用 frozen dataclass 定义 `steps`、`final_score`、`success`、`cost`、`average_step_gain`。 |
| `from_trace()` 计算 `steps` | PASS | `metrics.py:31-35` 优先读取 final state 的步数，无 final state 时从事件步数安全回退；规格示例和 `test_metrics.py:35` 均验证结果为 2。 |
| `from_trace()` 计算 `final_score` | PASS | `metrics.py:24-25,36` 按 trace 顺序提取 `EVALUATE` 分数并取最后值；无分数时返回 `0.0`。 |
| `from_trace()` 计算 `success` | PASS | `metrics.py:37-41` 对完成 trace 以最终状态 `SUCCEEDED` 为成功，未完成 trace 回退到最后一次 evaluation。`test_metrics.py:37` 覆盖成功结果。 |
| `from_trace()` 计算 `cost` | PASS | `metrics.py:26-30,50` 仅汇总 `ACT` 事件的 cost；`test_metrics.py:38` 验证 `0.25 + 0.5 = 0.75`。 |
| `from_trace()` 计算 `average_step_gain` | PASS | `metrics.py:42-44` 计算相邻 evaluation 分数增量的算术平均；零或一个分数时返回 `0.0`。`test_metrics.py:39` 验证 `[0.0, 0.5, 1.0]` 的平均增益为 `0.5`。 |
| 指标计算不修改状态 | PASS | `metrics.py:21-52` 仅执行读取、转换和局部聚合，不写入 trace、event payload 或 final state；`test_metrics.py:30-41` 提供基础回归断言。 |
| runner 将事件写入 memory | PASS | `runner.py:117-125` 通过统一 `_record_event()` 先写 trace，再把同一事件加入 memory；包括 `STOP` 在内的所有事件都经过该路径。 |
| runner 向兼容策略提供最近事件 | PASS | `runner.py:101-115` 读取有界 memory，并兼容位置参数、关键字参数和原有两参数策略；`test_runner.py:121-143` 验证两轮可见的历史事件。 |
| 保持 Task 4 阶段顺序 | PASS | `runner.py:48-73` 仍严格执行 `OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK`；`test_runner.py:63-79` 显式回归单轮完整顺序，memory 集成测试也验证第二轮决策前的事件顺序。 |
| 保持 Task 4 停止行为 | PASS | `runner.py:75-87,131-145` 仍在每轮反馈后检查停止条件，条件命中或安全上限到达时追加 `STOP` 并设置最终状态；成功、最大步数和 safety stop 测试均保留并通过。 |
| 保持既有策略接口兼容 | PASS | `policies.py:24-29,39-44` 新参数有默认值，原有 `decide(state, feedback)` 调用仍有效；`runner.py:107-115` 对两参数实现回退。`RecordingIncrementPolicy` 仍使用 Task 3 的两参数签名，`test_runner.py:82-98` 实际执行并通过。 |
| 有界状态 | PASS | `WorkingMemory` 由 maxlen 强制限制；runner 仍由 `safety_max_steps` 限制循环次数，不存在默认无限增长或无限循环。 |
| 可观察 trace | PASS | 新集成没有绕过 `LoopTrace.append()`；每个阶段、停止状态和原因继续保留在结构化事件中。 |
| 运行时仅使用标准库 | PASS | 新增运行时依赖只有 `collections.deque`、`dataclasses` 和 `inspect`，其余均为包内模块；`pyproject.toml` 的运行时 dependencies 仍为空。 |
| 未提前实现 CLI 或实验 | PASS | 当前工作区没有 `loop_engineering/cli.py`、`tests/test_cli.py` 或 `experiments/`；Task 6/实验功能未出现。 |

## 4. Code quality：APPROVED

`WorkingMemory` 实现小而直接，由 deque 自身提供淘汰语义，没有重复维护容量计数。`recent()` 返回新列表，不向调用者暴露内部 deque。

`MetricReport` 是不可变值对象，计算逻辑集中在 `from_trace()`，只依赖 trace 中已经可观察的 `EVALUATE`、`ACT` 和 final state。平均步增益使用首尾差除以区间数，数学上等价于所有相邻增量的算术平均。

runner 把 trace 与 memory 写入集中到 `_record_event()`，避免新增阶段漏写 memory。`_decide()` 没有捕获策略执行本身抛出的 `TypeError`，只使用签名绑定判断调用方式，因此不会把策略内部错误误判成接口兼容问题。原有两参数策略、支持第三个位置参数的策略，以及支持 `recent_events` 关键字参数的策略均能继续工作。

## 5. 测试覆盖与回归风险

### 新增行为覆盖

- `tests/test_memory.py` 覆盖容量淘汰、最近尾部查询、零 limit 和非法 capacity。
- `tests/test_metrics.py` 在一个用例中覆盖全部 5 个指标及基础非修改性断言。
- `tests/test_runner.py` 覆盖事件进入 memory、首轮/次轮策略可见历史，以及 memory 与当前 trace 的一致性。

### Task 4 回归覆盖

- 成功停止与最终状态；
- 最大步数停止、停止原因和完整阶段顺序；
- 上一轮 evaluation 到下一轮 feedback 的传递；
- 没有停止条件命中时的安全上限；
- 原有两参数策略实现继续可调用。

### 风险判断

整体回归风险为 **LOW**。memory 写入沿用统一事件追加路径，没有改变 action、evaluation、feedback 或停止条件的先后关系。主要剩余风险是上文所述的 memory 跨 `run()` 生命周期语义尚未明确，以及非修改性测试的快照不够深；两者均不影响当前单次运行和 Task 6 的计划接口。

## 6. 测试与报告可信度

使用报告指定的解释器重新执行：

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_memory.py tests/test_metrics.py tests/test_runner.py -q
.........                                                                [100%]
9 passed in 0.05s

C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
..........................                                               [100%]
26 passed in 0.88s
```

报告记录为 `9 passed in 0.05s` 和 `26 passed in 0.92s`。通过数量已精确复现；完整套件耗时相差 `0.04s`，属于正常环境和缓存波动。因此，报告中的测试结论可信。

验证环境为 Python 3.11.9、pytest 7.4.3。pytest 版本低于 `pyproject.toml` 声明的开发依赖 `pytest>=8.0`；当前结果证明代码在 pytest 7.4.3 下通过，但没有单独验证 pytest 8.x。测试只使用基础 pytest 能力，该偏差不改变本次通过结论。

当前工作区不是 Git 仓库，`git status` 和 `git log` 均返回「not a git repository」。因此无法独立核验报告中的「No Git commit was created」，也无法通过 diff 证明 Task 5 相对 Task 4 的精确变更边界。当前文件系统检查可以确认没有提前加入 CLI 或实验文件。

## 7. Task 6 准入结论

**允许进入 Task 6。**

Task 5 的核心规格、Task 4 回归接口和全局约束均通过审查，报告中的 `9 passed` 与 `26 passed` 已独立复现。进入 Task 6 前没有必须修改的实现项。建议在后续测试维护中加强 `MetricReport.from_trace()` 的深度非修改性断言，并在 CLI/实验文档中明确 memory 的运行生命周期。
