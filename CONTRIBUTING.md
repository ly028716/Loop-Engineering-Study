# Contributing

感谢你关注 Loop Engineering Study。这个仓库优先服务于可验证的学习和实验，
欢迎补充概念、实验、测试和文档。

## 开始之前

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

## 提交原则

- 保持实验本地、可复现，并避免引入不必要的外部服务。
- 新的运行时行为应包含测试和结构化 Trace 说明。
- 新的指标需要明确含义、边界条件和文档。
- 不要把 `.loop/runs`、coverage 或本地环境文件提交到仓库。
- README、docs 和 theory 中的结论应与当前实现一致。

## Pull Request

请在描述中说明问题、方案、验证命令和任何行为边界。提交前至少运行：

```powershell
python -m pytest -q
python -m build --wheel
```

提交消息建议使用 Conventional Commits，例如 `docs: explain artifact replay`。
