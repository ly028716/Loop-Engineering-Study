# Convergence and Stopping Design

## Goal

为 Loop Engineering Study 增加显式的无进展停止条件，并通过收敛、停滞和振荡三种
确定性循环展示不同停止原因。

## Scope

本阶段新增一个 `NoProgress` 停止条件、一个对比实验、测试和学习文档。现有
`SuccessReached`、`MaxSteps`、`LoopRunner` 和 Artifact 格式保持兼容；不引入网络、
LLM、数据库或异步调度。

## NoProgress condition

`NoProgress(window: int, min_score_gain: float = 0.0)` 读取历史中的 `EVALUATE`
事件：

- `window` 必须至少为 `1`；`min_score_gain` 不能为负数；
- 当评估样本不足时继续运行；
- 当最近窗口内每一次相邻得分提升都不超过 `min_score_gain` 时停止；
- 停止结果为 `status="STOPPED"`，原因是
  `No progress for {window} evaluations`；
- 正向得分提升超过阈值时继续运行。

这个条件只负责识别无进展，不判断目标是否达成。`SuccessReached` 仍然负责成功
停止，`MaxSteps` 仍然负责资源上限；它们的顺序由实验显式配置。

## Experiment design

入口为 `experiments/convergence_stopping.py`，比较三种模式：

1. `converging`：使用 `NumericAction` 和固定增量策略，数值持续接近目标，最终由
   `SuccessReached` 停止。
2. `stalled`：使用不改变数值的动作，评估分数持续不变，最终由
   `NoProgress(window=3)` 停止。
3. `oscillating`：使用在两个数值之间往返的动作，分数会升降而不是持续无进展，
   最终由 `MaxSteps` 停止。

三种模式共享确定性目标、`GoalEvaluator`、Artifact 保存方式，并输出：

- `mode`
- `steps`
- `final_score`
- `success`
- `score_history`
- `stop_reason`
- `artifact_path`

## Learning documentation

新增 `docs/convergence-stopping.md`，解释收敛、停滞、振荡的区别，说明为什么成功、
无进展和最大步数是不同的停止信号，并给出实验和 Artifact 检查命令。

同时更新 `docs/experiments.md`、中英文 README 和项目进度记录。

## Testing

新增测试覆盖：

- `NoProgress` 的参数校验；
- 样本不足时继续；
- 连续无提升时停止；
- 得分有提升时继续；
- 三种实验模式的停止状态、原因和 Artifact 加载；
- 现有停止条件和全量测试保持通过。

## Non-goals

- 不新增通用收敛数学库或统计显著性分析。
- 不修改现有事件结构和指标字段。
- 不处理跨运行收敛、长期记忆或外部环境变化。
- 不把实验 Artifact 提交到 Git。

## Acceptance criteria

- `NoProgress` 能被独立单元测试验证，并能作为现有 `StopCondition` 使用。
- 三种模式可以从仓库根目录直接运行并生成三个可加载 Artifact。
- `STOP` 事件清楚区分成功、无进展和最大步数停止。
- 完整 pytest 测试通过，运行产物继续被 `.gitignore` 忽略。
