# Final Review Fixes Implementation Plan

> **执行者说明：** 在当前指定工作区内按 `superpowers-zh:executing-plans`
> 执行；遵从用户要求，不创建 worktree、不执行 git commit、不修改 `.git` 元数据。

**目标：** 修复最终审查 I-1、I-2、M-1、M-2，使安装、统一 run artifact
回放、三个直接实验和当前概念文档达到可复现验收状态。

**架构：** 新增一个只依赖标准库的 run artifact 模块，作为 CLI 和实验唯一的
JSON 保存/加载边界；保留 CLI `write_trace()` 和 stdout 摘要兼容。setuptools
继续使用平铺布局，但显式发现两个公开顶层包。

**技术栈：** Python 3.11、标准库、setuptools、pytest。

---

### 任务 1：先建立失败的验收测试

**文件：**
- 创建：`tests/test_artifacts.py`
- 创建：`tests/test_packaging.py`
- 修改：`tests/test_cli.py`
- 修改：`tests/test_experiments.py`

- [x] 添加 UTF-8 artifact、完整 metrics、`LoopTrace`/`MetricReport`
  round-trip 测试。
- [x] 更新 CLI 测试，保持 stdout 字段不变并通过共享 loader 校验 artifact。
- [x] 更新三个直接实验测试，断言稳定 `.loop/runs/*.json` 路径、输出
  `artifact_path`、文件存在且可加载。
- [x] 添加普通包导入不改变 `sys.path` 的隔离 subprocess 测试。
- [x] 添加显式包发现测试，并在最终验证中从临时干净源码副本构建 wheel，检查其同时包含
  `loop_engineering` 与 `experiments`。
- [x] 运行定向测试，预期因缺少 artifact API、metrics、实验产物、显式包发现
  和条件 bootstrap 而失败。

### 任务 2：实现统一 run artifact 契约

**文件：**
- 创建：`loop_engineering/artifacts.py`
- 修改：`loop_engineering/cli.py`

- [x] 实现
  `save_run_artifact(path, trace, metrics=None) -> Path`，写入 UTF-8 JSON，
  顶层固定包含 `events`、`final_state`、`metrics`。
- [x] 实现
  `load_run_artifact(path) -> tuple[LoopTrace, MetricReport]`，恢复领域对象。
- [x] 让 CLI `write_trace()` 委托共享保存接口，保持原签名和 stdout
  `trace_path` 摘要不变。
- [x] 运行 artifact 与 CLI 定向测试，预期全部通过。

### 任务 3：统一三个直接实验的落盘入口并修复 bootstrap

**文件：**
- 修改：`experiments/_bootstrap.py`
- 修改：`experiments/basic_loop.py`
- 修改：`experiments/retry_loop.py`
- 修改：`experiments/repair_loop.py`

- [x] 在共享 bootstrap 中保存
  `.loop/runs/basic_loop.json`、`retry_loop.json`、`repair_loop.json`，
  并在原摘要之后打印绝对 `artifact_path`。
- [x] 仅在 `__package__` 为空的直接脚本分支调用
  `prepare_script_imports()`；普通包导入不改 `sys.path`。
- [x] 运行实验与导入定向测试，预期全部通过。

### 任务 4：修复包发现与概念文档

**文件：**
- 修改：`pyproject.toml`
- 修改：`docs/concepts.md`

- [x] 在 `[tool.setuptools.packages.find]` 中显式包含
  `loop_engineering*` 和 `experiments*`。
- [x] 将概念页更新为当前已实现首版，并链接模型、runner、策略、动作、
  评估、停止、记忆、指标、artifact、CLI 和实验模块。
- [x] 运行 packaging 与项目文档定向测试，预期全部通过。

### 任务 5：最终验证并形成证据报告

**文件：**
- 创建：`docs/superpowers/sdd/final-fix-report.md`

- [x] 运行完整 pytest。
- [x] 在临时干净源码副本执行 wheel build，并从 wheel 隔离导入两个包及
  `loop-engineering` 命令入口。
- [x] 运行 CLI smoke，并用共享 loader 检查完整 metrics。
- [x] 运行三个直接实验，并逐个加载其 artifact。
- [x] 单独运行 artifact loader round-trip 测试。
- [x] 执行占位扫描。
- [x] 把精确命令、退出码和结果写入最终修复报告；不执行 git commit。
