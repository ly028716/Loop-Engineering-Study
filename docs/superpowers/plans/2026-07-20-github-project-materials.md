# GitHub Project Materials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 补齐 Loop-Engineering-Study 作为独立开源学习项目所需的入口文档、工程可信度资料和社区协作文件，并推送到 GitHub。

**Architecture:** 保持现有 Python 运行时与实验代码不变；通过 README、docs、theory 和 GitHub 元文件解释当前能力、运行方式与后续研究边界。CI 只验证当前可复现的安装、测试和构建流程。

**Tech Stack:** Markdown, GitHub Actions, Python 3.11–3.13, pytest, setuptools。

## Global Constraints

- 只描述当前已实现能力，不宣称已实现 LLM、在线服务或完整 Agent 平台。
- CI 必须使用项目现有的 `.[dev]` 安装方式和 `python -m pytest -q`。
- 不将 `.coverage`、`.pytest_cache` 或 `.loop/runs` 运行产物提交到仓库。
- 完成后必须运行完整测试、构建检查，并提交、推送到 `origin/master`。

### Task 1: 清理仓库产物并补充开源基础文件

**Files:** `.gitignore`, `LICENSE`, `CHANGELOG.md`

- [ ] 更新忽略规则，覆盖 Python 缓存、coverage、pytest 缓存和实验运行产物。
- [ ] 添加 MIT 许可证，版权主体使用 `ly028716`，年份使用 2026。
- [ ] 添加 0.1.0 初始版本变更记录，列出当前运行时、实验、文档和测试覆盖。
- [ ] 检查 `git status`，确认本地产物不再显示为待提交文件。

### Task 2: 重写 GitHub 入口 README

**Files:** `README.md`, `README.zh-CN.md`

- [ ] 将项目定位明确为可执行的 Loop Engineering 学习实验室。
- [ ] 添加当前能力、快速开始、CLI 和三个实验的复制运行命令。
- [ ] 添加文档导航、研究边界、质量状态和贡献入口。
- [ ] 中英文 README 保持结构和事实一致。

### Task 3: 补充架构、指标和回放文档

**Files:** `docs/architecture.md`, `docs/metrics.md`, `docs/replay.md`

- [ ] 解释 state → decision → action → evaluation → feedback → stopping 的数据流。
- [ ] 解释 `events`、`final_state`、`metrics` artifact 的结构和使用场景。
- [ ] 说明当前指标定义、确定性边界、回放限制和研究演进路径。

### Task 4: 增加 CI 与社区协作模板

**Files:** `.github/workflows/ci.yml`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] CI 在 Python 3.11、3.12、3.13 上安装开发依赖、运行测试并构建 wheel。
- [ ] 协作文档说明本地验证、实验边界和提交要求。
- [ ] 添加最小可用的行为准则、安全报告说明和 Issue/PR 模板。

### Task 5: 验证、提交和推送

- [ ] 运行 `python -m pytest -q`。
- [ ] 运行 `python -m build --wheel` 或等价构建检查。
- [ ] 检查 diff、工作区状态和提交内容。
- [ ] 使用 Conventional Commit 提交并推送 `origin/master`。
