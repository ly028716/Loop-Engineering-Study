# Trace 差异分析设计

## 目标

为两次确定性 Loop 运行提供只读的 Trace 差异分析能力。首版以
“诊断 → 修复 → 验证”实验生成的基线与修复后 Artifact 为输入，定位两条
Trace 的首个分歧，并汇总最终状态与指标变化。

该功能用于解释修复从哪里开始改变运行行为；它不重新执行 Action、不修改
Artifact，也不把后续连锁变化误判为多个独立根因。

## 范围

### 包含

- 新增纯分析模块 `loop_engineering.trace_diff`。
- 顺序对齐两条 `LoopTrace`，定位首个事件或字段分歧。
- 比较完整事件序列后，继续比较 `final_state` 与 `MetricReport`。
- 新增 `experiments.trace_diff_analysis`，对三组诊断修复案例输出结构化报告。
- 为公共比较接口与实验报告添加单元测试。

### 不包含

- 动态规划、编辑距离或非顺序事件匹配。
- 对任意外部副作用的重放。
- Artifact JSON 格式变更。
- 自动判断修复方案的正确性；沿用现有 `repair_succeeded` 结论。

## 模块设计

### `loop_engineering.trace_diff`

新增下列稳定、JSON 可序列化的数据模型与入口：

- `TraceDifference`：记录首分歧的位置和内容。字段包括比较范围、事件索引、
  `step`、`phase`、字段路径、基线值与修复后值。
- `TraceComparison`：包含 `identical`、`first_difference`、两侧事件数量、
  最终状态差异与指标差异。
- `compare_traces(baseline, repaired, baseline_metrics, repaired_metrics)`：
  对两条 Trace 及其指标进行确定性比较，返回 `TraceComparison`。

模块只依赖既有领域模型和指标模型；不依赖实验代码、文件系统或 CLI。

## 比较规则

1. 按事件索引顺序对齐基线与修复后的事件。
2. 对同一索引的事件，依次比较 `step`、`phase`、`payload`。
3. `payload` 使用递归字段比较：字典键按稳定顺序检查；标量值、列表长度、
   列表元素和缺失字段均可构成首分歧。
4. 若两条 Trace 的公共事件前缀完全相同但长度不同，首个缺失或新增事件构成
   首分歧。
5. 若事件完全一致，则比较 `final_state`；若仍一致，再比较 `MetricReport`。
6. 一旦定位到首分歧，不再枚举后续事件或字段差异。

空事件 Trace、`None` 最终状态、失败运行和不同长度 Trace 都是有效输入。

## 实验与报告

新增 `experiments/trace_diff_analysis.py`：

1. 调用现有 `run_repair_loop` 生成三组基线/修复后 Artifact。
2. 逐对加载 Artifact 并调用 `compare_traces`。
3. 为 `action_failure`、`stalled_progress`、`tight_budget` 保持既有案例顺序。
4. 将汇总报告写入
   `.loop/runs/trace-diff-analysis/report.json`，同时向标准输出打印 JSON。

每个案例包含案例名、两份 Artifact 路径、已有 `repair_succeeded`、比较结果，
以及基线和修复后状态与指标摘要。报告的键与案例顺序必须稳定，方便学习者
对照运行结果和测试断言。

## 错误处理

- 文件读取错误、无效 JSON 与不兼容 Artifact 仍由既有 `load_run_artifact` 抛出，
  不在差异分析模块中吞掉或重写。
- 公共比较函数不要求 Trace 成功完成，也不把没有差异视为错误。
- 不支持的值类型按 Python 相等性比较，确保分析函数对已有 payload 保持通用。

## 测试与验收

单元测试至少覆盖：

- 完全相同的 Trace、最终状态和指标。
- Payload 首字段分歧。
- `step` 或 `phase` 分歧。
- 公共前缀相同但事件数量不同。
- 仅最终状态分歧。
- 仅指标分歧。
- 三组修复案例均产生首分歧，输出可经 `json.dumps` 序列化，且案例顺序稳定。

验收命令为：

```powershell
python -m pytest -q
python experiments/trace_diff_analysis.py
```

## 设计边界

顺序对齐故意优先于复杂的序列匹配。当前学习案例的基线与修复运行共享相同的
生命周期阶段，首个顺序分歧最容易解释修复如何影响运行。未来如需处理分支、
重试插入或异步事件，可在保留当前公共接口的前提下新增专门的对齐策略。
