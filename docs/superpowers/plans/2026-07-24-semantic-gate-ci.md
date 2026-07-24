# Semantic Gate CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add an independent GitHub Actions semantic gate that uploads deterministic evidence.

**Architecture:** Keep the current Python test/build matrix unchanged. A new semantic-gate job depends on test, runs the existing regression gate on Python 3.11, and uploads its output even after a failure. A pytest text contract protects the workflow requirements.

**Tech Stack:** GitHub Actions, Python 3.11, pytest, pathlib.

## Global Constraints

- Do not change the existing test job or its Python 3.11–3.13 matrix.
- The semantic-gate job depends on test, uses Python 3.11, installs development dependencies, and runs python experiments/regression_gate.py.
- Artifact name is semantic-gate-evidence and its path is .loop/runs/regression-gate/.
- The upload step must run with if: always().
- Do not modify the regression gate implementation or GitHub branch-protection settings.

---

## Task 1: Add a failing workflow contract test, then the new CI job

**Files:**

- Create: tests/test_ci_workflow.py
- Modify: .github/workflows/ci.yml

**Interfaces:**

- Consumes: CI workflow text at .github/workflows/ci.yml.
- Produces: a separately visible semantic-gate job.

- [ ] **Step 1: Write the failing test**

Create tests/test_ci_workflow.py:

~~~python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_has_independent_semantic_gate_with_evidence_upload() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "semantic-gate:" in workflow
    assert "needs: test" in workflow
    assert 'python-version: "3.11"' in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python experiments/regression_gate.py" in workflow
    assert "name: semantic-gate-evidence" in workflow
    assert "path: .loop/runs/regression-gate/" in workflow
    assert "if: always()" in workflow
    assert "uses: actions/upload-artifact@v4" in workflow
~~~

- [ ] **Step 2: Verify RED**

Run: python -m pytest tests/test_ci_workflow.py -q

Expected: failure because semantic-gate and its upload are absent.

- [ ] **Step 3: Add the independent semantic-gate job**

Append this YAML without changing the existing test job:

~~~yaml
  semantic-gate:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Install project and development dependencies
        run: python -m pip install -e ".[dev]"
      - name: Run semantic regression gate
        run: python experiments/regression_gate.py
      - name: Upload semantic gate evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: semantic-gate-evidence
          path: .loop/runs/regression-gate/
          if-no-files-found: warn
~~~

- [ ] **Step 4: Verify GREEN**

Run: python -m pytest tests/test_ci_workflow.py -q

Expected: 1 passed.

- [ ] **Step 5: Commit**

~~~powershell
git add .github/workflows/ci.yml tests/test_ci_workflow.py
git commit -m "ci: add semantic regression gate"
~~~

## Task 2: Document the CI gate and verify its local behavior

**Files:**

- Modify: docs/regression-gate.md
- Modify: README.md
- Modify: docs/superpowers/sdd/progress.md

**Interfaces:**

- Consumes: semantic-gate CI job and .loop/runs/regression-gate/ evidence.
- Produces: downloadable-evidence guidance for contributors.

- [ ] **Step 1: Add CI documentation**

Append this section to docs/regression-gate.md:

~~~markdown
## 独立 CI 门禁

GitHub Actions 在测试矩阵通过后运行独立的 semantic-gate job。该 job 使用
Python 3.11 执行 python experiments/regression_gate.py；任一语义契约失败都会使
该 job 失败。

无论成功或失败，工作流都会上传名为 semantic-gate-evidence 的 Artifact。
下载后查看 .loop/runs/regression-gate/ 下的 benchmark、sensitivity、diagnostics
和 repair-loop 子目录，以及它们保存的可回放 Trace 与报告。

仓库代码只提供该检查；是否在 GitHub 分支保护规则中把 semantic-gate 设为必需状态，
由仓库管理员在 GitHub 设置中决定。
~~~

- [ ] **Step 2: Update README and progress**

Add this sentence after the Development commands in README.md:

~~~markdown
CI runs the Python test-and-build matrix first, then a separate Python 3.11
semantic gate that uploads semantic-gate-evidence for diagnosis.
~~~

Append a progress entry to docs/superpowers/sdd/progress.md that records the independent semantic-gate job, its always evidence upload, and the final pytest count obtained in Step 3.

- [ ] **Step 3: Run local gate and full verification**

Run:

~~~powershell
python experiments/regression_gate.py
python -m pytest -q
git diff --check
~~~

Expected: the first command prints a passed true result and creates .loop/runs/regression-gate/; all tests pass; whitespace check has no output.

- [ ] **Step 4: Commit documentation**

~~~powershell
git add docs/regression-gate.md README.md docs/superpowers/sdd/progress.md
git commit -m "docs: explain semantic gate CI"
~~~

