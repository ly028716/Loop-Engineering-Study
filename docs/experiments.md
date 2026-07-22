# Experiments

所有实验都在本地运行，只依赖项目代码和 Python 标准库。建议按以下顺序进行：

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
python experiments/feedback_strategies.py
```

## 基础实验

`basic_loop.py` 展示一个稳定的目标逼近循环：策略每轮增加固定值，直到达到目标。

## 重试实验

`retry_loop.py` 注入一次动作失败。评估器将失败转换为
`retry_required` 反馈，策略读取该反馈后选择更大的下一步动作。

## 修复实验

`repair_loop.py` 展示动作结果和评估报告不一致的情况：状态可能已经达到目标，
但评估器仍然报告失败。这个实验提醒我们不能只看最终值，必须同时检查评估器和
停止条件。

## 反馈策略对比

`feedback_strategies.py` 使用统一配置比较 `fixed`、`error_aware` 和 `memory_aware`
三种策略。详细问题、指标和 Artifact 查看方式见
[feedback-strategies.md](feedback-strategies.md)。

每个脚本都会输出摘要，并将完整 Trace 写入 `.loop/runs/`。运行产物可以通过
`loop_engineering.artifacts.load_run_artifact()` 加载。
