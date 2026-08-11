# Public Learning Release Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository reproducible, easier to navigate as a learning project, and protected by automated documentation checks.

**Architecture:** Keep runtime behavior unchanged. Improve package metadata and public documentation, then add a small standard-library checker whose test coverage and CI invocation make documentation regressions visible.

**Tech Stack:** Python 3.11+, setuptools, pytest, GitHub Actions, Markdown.

## Global Constraints

- Python support remains `>=3.11`.
- Runtime dependencies remain empty.
- The repository is Chinese-first for detailed learning documentation.
- Do not create Git tags, GitHub Releases, or modify repository settings.
- Preserve all existing `docs/superpowers/` historical files in place.

---

### Task 1: Make documented developer commands installable

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Consumes: `[project.optional-dependencies].dev` from `pyproject.toml`.
- Produces: a `dev` extra containing `pytest>=8.0` and `build>=1.2`.

- [x] **Step 1: Write the failing test**

```python
def test_dev_extra_includes_documented_verification_tools() -> None:
    dependencies = pyproject["project"]["optional-dependencies"]["dev"]
    assert "build>=1.2" in dependencies
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_packaging.py -q`
Expected: FAIL because `build>=1.2` is absent.

- [x] **Step 3: Write minimal implementation**

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "build>=1.2"]
```

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_packaging.py -q`
Expected: PASS.

### Task 2: Add a portable documentation integrity checker

**Files:**
- Create: `scripts/check_docs.py`
- Create: `tests/test_docs_integrity.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `check_repository(root: Path) -> list[str]`, returning human-readable failures.
- Consumes: repository Markdown files and relative Markdown link targets.

- [x] **Step 1: Write failing tests**

```python
def test_check_repository_accepts_valid_utf8_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("[Guide](docs/guide.md)", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide", encoding="utf-8")
    assert check_repository(tmp_path) == []
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_docs_integrity.py -q`
Expected: FAIL because `check_repository` does not exist.

- [x] **Step 3: Write minimal implementation**

```python
def check_repository(root: Path) -> list[str]:
    errors: list[str] = []
    for markdown_file in root.rglob("*.md"):
        text = markdown_file.read_text(encoding="utf-8")
        # Report undecodable files and missing local Markdown targets.
    return errors
```

- [x] **Step 4: Add CI invocation and verify tests pass**

Run: `python -m pytest tests/test_docs_integrity.py -q`
Expected: PASS; CI runs `python scripts/check_docs.py` before pytest.

### Task 3: Improve public learning and release documentation

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/learning-path.md`
- Create: `docs/release-checklist.md`
- Create: `docs/superpowers/README.md`
- Modify: `tests/test_project_contract.py`

**Interfaces:**
- Consumes: the CLI artifact and the three baseline experiments.
- Produces: a beginner-first route, language expectations, Trace preview,
  release checklist, and archive explanation.

- [x] **Step 1: Write failing contract tests**

```python
def test_readme_exposes_beginner_route_and_trace_preview() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "30-minute beginner route" in readme
    assert "OBSERVE" in readme and "STOP" in readme
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_project_contract.py -q`
Expected: FAIL because the new public-learning wording is absent.

- [x] **Step 3: Write minimal documentation changes**

```markdown
## 30-minute beginner route

1. Run the deterministic CLI example.
2. Run `basic_loop`, `retry_loop`, and `repair_loop`.
3. Inspect the generated artifact and continue to advanced experiments.
```

- [x] **Step 4: Run contract tests and the documentation checker**

Run: `python -m pytest tests/test_project_contract.py -q && python scripts/check_docs.py`
Expected: PASS with no documentation errors.
