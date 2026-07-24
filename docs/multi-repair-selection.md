# 多修复方案选择

本实验对同一诊断问题声明多个确定性修复候选，分别真实重跑并保存 Artifact，再按运行证据选择方案。

## 运行实验

```powershell
python experiments/multi_repair_selection.py
```

汇总报告写入 `.loop/runs/multi-repair-selection/report.json`。三个案例均包含两项候选和独立 Artifact。

## 排序规则

候选按以下顺序稳定排序：修复后是否成功、是否消除全部目标诊断、总成本、执行步数、候选声明顺序。

## 如何阅读报告

每个案例的 `candidates` 已按最终排名排列。`selected_candidate` 是第一名，`selection_reason` 说明固定决胜规则，`repair_succeeded` 表示选中候选成功且不再含有目标诊断。

## 解释边界

选择器只评估预先声明并已运行完成的候选，不搜索未知策略、Action 或预算组合，也不会把选择结果写回运行时策略。
