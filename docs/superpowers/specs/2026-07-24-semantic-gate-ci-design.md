# 语义门禁独立 CI 步骤设计

## 目标

将现有 `experiments/regression_gate.py` 从普通 pytest 覆盖中提升为 GitHub Actions 的独立 `semantic-gate` job，使其具有单独状态、可下载的诊断 Artifact，并在失败时阻断 CI。

## 范围

修改现有 `.github/workflows/ci.yml`，新增工作流结构测试和文档说明。保留既有 Python 3.11、3.12、3.13 测试矩阵与 wheel 构建步骤，不修改回归门禁的四项语义契约，不配置 GitHub 分支保护规则。

## 工作流设计

现有 `test` job 保持不变。新增：

```yaml
semantic-gate:
  needs: test
  runs-on: ubuntu-latest
```

该 job 固定使用 Python 3.11，并执行：

1. checkout；
2. setup-python（Python 3.11，pip cache）；
3. 安装 `python -m pip install -e ".[dev]"`；
4. 运行 `python experiments/regression_gate.py`；
5. 通过 `actions/upload-artifact@v4` 上传 `.loop/runs/regression-gate/`，Artifact 名称为 `semantic-gate-evidence`，且步骤设置 `if: always()`。

`needs: test` 确保只有测试矩阵成功后才执行语义门禁。门禁自身失败会使 `semantic-gate` 失败；上传步骤仍会运行，保留 benchmark、sensitivity、diagnostics 与 repair-loop 的可回放诊断材料。

## 安全与确定性

语义门禁复用既有确定性实验。它不读取 API Key、不调用外部模型适配器，也不需要网络服务；GitHub Actions 网络仅用于常规 checkout、依赖安装和 Artifact 上传。

## 验证

新增 `tests/test_ci_workflow.py`，使用标准库读取 YAML 文本并断言：

- 存在 `semantic-gate` job；
- job 依赖 `test`；
- 使用 Python 3.11；
- 安装项目开发依赖；
- 运行 `python experiments/regression_gate.py`；
- 以 `if: always()` 上传 `.loop/runs/regression-gate/`；
- Artifact 名称为 `semantic-gate-evidence`。

本地验证运行：

```powershell
python experiments/regression_gate.py
python -m pytest -q
```

并确认门禁报告目录生成、四项检查通过与完整测试套件通过。

## 文档

更新 `docs/regression-gate.md` 和 README 的开发说明，说明独立 `semantic-gate` 状态、Artifact 名称及下载用途，并明确分支保护规则不属于仓库代码改动范围。

## 验收标准

- GitHub Actions 显示独立 `semantic-gate` job；
- 它仅在测试矩阵成功后运行，并因门禁失败而失败；
- 成功或失败时均上传 `semantic-gate-evidence`；
- 工作流结构由自动化测试守护；
- 本地门禁和全量 pytest 通过。

