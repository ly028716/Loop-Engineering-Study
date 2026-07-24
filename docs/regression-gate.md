# 回归门禁

回归门禁把项目的关键学习能力固化为可执行的语义契约。它不是完整 JSON 快照，也不替代 benchmark 的性能解释；它用于发现后续改动是否破坏了已经验证的行为。

## 运行门禁

```powershell
python experiments/regression_gate.py
```

门禁输出 `passed` 与逐条 `checks`。每条检查都包含名称、通过状态和证据；任一契约失败时脚本以非零退出码结束。子实验产物保存在 `.loop/runs/regression-gate/` 的独立目录中。

## 四组语义契约

- `benchmark`：保护 20 次运行、四种策略汇总，以及 `adaptive` 优于 `fixed` 的当前基准能力。
- `sensitivity`：保护 9 个配置、36 条运行记录、参数隔离和目标距离扫描的稳定边界。
- `diagnostics`：保护四个诊断案例、四类诊断标签及可读取的 Artifact/报告。
- `repair_loop`：保护三个修复案例的成功完成和目标诊断消除。

## 解释边界

门禁只断言这些确定性实验的关键语义，不比较完整 Artifact 内容，不自动修复失败，也不对真实服务性能作结论。若门禁失败，应先阅读 `evidence`，再回放对应子目录中的 Trace Artifact 定位行为变化。

## 独立 CI 门禁

GitHub Actions 在测试矩阵通过后运行独立的 `semantic-gate` job。该 job 使用 Python 3.11 执行 `python experiments/regression_gate.py`；任一语义契约失败都会使该 job 失败。

无论成功或失败，工作流都会上传名为 `semantic-gate-evidence` 的 Artifact。下载后查看 `.loop/runs/regression-gate/` 下的 benchmark、sensitivity、diagnostics 和 repair-loop 子目录，以及它们保存的可回放 Trace 与报告。

仓库代码只提供该检查；是否在 GitHub 分支保护规则中把 `semantic-gate` 设为必需状态，由仓库管理员在 GitHub 设置中决定。
