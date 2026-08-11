# Loop Engineering Course Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a deterministic 45-minute code-repair course that teaches developers to diagnose and improve an Agent loop while preserving the reusable framework.

**Architecture:** A deterministic code-repair domain adapts candidate repairs and test-style evaluation to the existing loop interfaces. Course documents become the public entry; existing numeric and integration experiments remain behind reference and advanced indexes.

**Tech Stack:** Python 3.11+, standard library, pytest, setuptools, Markdown, GitHub Actions.

## Global Constraints

- Python support remains `>=3.11`; runtime dependencies remain empty.
- Core commands are local, deterministic, and need no credentials, network calls, or arbitrary shell execution.
- `loop_engineering/` remains domain-neutral and must not import code-repair types.
- Preserve all current experiments, historical documents, and advanced adapters.
- Do not create Git tags, GitHub Releases, or modify remote repository settings.

---

### Task 1: Create the deterministic code-repair domain

**Files:**
- Create: `examples/code_repair/__init__.py`
- Create: `examples/code_repair/domain.py`
- Create: `tests/test_code_repair_domain.py`

**Interfaces:**
- Produces `RepairCase`, `RepairCandidate`, `CandidateRepairAction`, `TestCaseEvaluator`, `RepeatedCandidatePolicy`, `FeedbackAwareRepairPolicy`, `boundary_repair_case()`, and `initial_repair_state()`.
- `CandidateRepairAction.apply()` records `candidate_name`, `tests_passed`, and `failed_inputs` in `LoopState.metadata`; it never edits a file.
- `TestCaseEvaluator.evaluate()` exposes `tests_passed`, `failed_test_count`, `failed_input`, and `recommended_candidate` in `Evaluation.signals`.

- [ ] **Step 1: Write the failing tests**

```python
def test_evaluator_rejects_a_plausible_but_wrong_candidate() -> None:
    case = boundary_repair_case()
    result = CandidateRepairAction(case).apply(
        initial_repair_state(), Decision("apply_candidate", {"candidate": "off_by_one"})
    )
    evaluation = TestCaseEvaluator(case).evaluate(initial_repair_state(), result)
    assert result.success is True
    assert evaluation.success is False
    assert evaluation.signals["failed_test_count"] == 1
```

- [ ] **Step 2: Run red verification**

Run: `python -m pytest tests/test_code_repair_domain.py -q`

Expected: collection fails because `examples.code_repair.domain` is absent.

- [ ] **Step 3: Implement the smallest boundary**

```python
class CandidateRepairAction(Action):
    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        candidate = self.case.candidates[str(decision.parameters["candidate"])]
        failures = tuple(value for value, expected in self.case.test_cases
                         if candidate.transform(value) != expected)
        return ActionResult(
            state=state.with_value(1.0 if not failures else 0.0,
                                   candidate_name=candidate.name,
                                   tests_passed=not failures,
                                   failed_inputs=failures),
            success=True,
            cost=1.0,
        )
```

- [ ] **Step 4: Run green verification**

Run: `python -m pytest tests/test_code_repair_domain.py -q`

Expected: PASS; action success and evaluator success are demonstrably separate.

- [ ] **Step 5: Commit**

```powershell
git add examples/code_repair tests/test_code_repair_domain.py
git commit -m "feat: add deterministic code repair domain"
```

### Task 2: Add baseline and three one-variable experiments

**Files:**
- Create: `experiments/code_repair/__init__.py`
- Create: `experiments/code_repair/_bootstrap.py`
- Create: `experiments/code_repair/baseline.py`
- Create: `experiments/code_repair/evaluator_signal.py`
- Create: `experiments/code_repair/feedback_strategy.py`
- Create: `experiments/code_repair/stopping_policy.py`
- Create: `tests/test_code_repair_experiments.py`

**Interfaces:**
- Every experiment exposes `run() -> LoopTrace` and writes direct-script Artifacts below `.loop/runs/code-repair/`.
- Baseline repeats `off_by_one` and stops at `MaxSteps(3)`; feedback strategy changes only policy and selects `fix_boundary`; stopping policy changes only to `NoProgress` and stops before a budget of 5.

- [ ] **Step 1: Write the failing tests**

```python
def test_feedback_strategy_succeeds_on_the_second_candidate() -> None:
    trace = feedback_strategy.run()
    decisions = [event.payload for event in trace.events if event.phase == "DECIDE"]
    assert [item["parameters"]["candidate"] for item in decisions] == ["off_by_one", "fix_boundary"]
    assert trace.final_state.status == "SUCCEEDED"


def test_no_progress_stops_before_budget() -> None:
    trace = stopping_policy.run()
    assert trace.final_state.step < 5
    assert trace.events[-1].payload["reason"] == "No progress for 2 evaluations"
```

- [ ] **Step 2: Run red verification**

Run: `python -m pytest tests/test_code_repair_experiments.py -q`

Expected: collection fails because `experiments.code_repair` is absent.

- [ ] **Step 3: Implement the nested runner modules**

```python
def project_root(script_file: str) -> Path:
    for parent in Path(script_file).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError("Could not locate project root")
```

Use the helper in the nested bootstrap for direct scripts. Assemble all four runs with the same case/action and alter only the named evaluator, policy, or stop condition.

- [ ] **Step 4: Run green verification and direct scripts**

Run: `python -m pytest tests/test_code_repair_experiments.py -q`

Run: `python experiments/code_repair/baseline.py`

Run: `python experiments/code_repair/feedback_strategy.py`

Expected: tests PASS; baseline stops and feedback strategy succeeds with Artifacts.

- [ ] **Step 5: Commit**

```powershell
git add experiments/code_repair tests/test_code_repair_experiments.py
git commit -m "feat: add code repair learning experiments"
```

### Task 3: Write the 45-minute learner route

**Files:**
- Create: `course/01-baseline.md`
- Create: `course/02-read-the-trace.md`
- Create: `course/03-improve-the-loop.md`
- Create: `tests/test_course_contract.py`

**Interfaces:**
- The route consumes Task 2 commands and Artifacts.
- It produces a failed baseline, Trace diagnosis, three single-variable experiments, before/after evidence, and a framework mapping exercise.

- [ ] **Step 1: Write failing course contract tests**

```python
def test_course_starts_from_the_failed_code_repair_baseline() -> None:
    lesson = (PROJECT_ROOT / "course" / "01-baseline.md").read_text(encoding="utf-8")
    assert "experiments/code_repair/baseline.py" in lesson
    assert "Action succeeded" in lesson
    assert "evaluation failed" in lesson
```

- [ ] **Step 2: Run red verification**

Run: `python -m pytest tests/test_course_contract.py -q`

Expected: FAIL because `course/` documents do not exist.

- [ ] **Step 3: Write the learner documents**

`01-baseline.md` gives one command, a Trace excerpt, and the action-versus-evaluation question. `02-read-the-trace.md` requires the learner to read evaluator signal, feedback, and stop reason before executing three experiments. `03-improve-the-loop.md` requires one policy or stopping change, before/after Artifacts, and a component-to-framework checklist.

- [ ] **Step 4: Run green verification**

Run: `python -m pytest tests/test_course_contract.py -q`

Run: `python scripts/check_docs.py`

Expected: PASS with valid links and required learner evidence.

- [ ] **Step 5: Commit**

```powershell
git add course tests/test_course_contract.py
git commit -m "docs: add code repair Loop Engineering course"
```

### Task 4: Make the course the public entry and index retained material

**Files:**
- Modify: `README.zh-CN.md`
- Modify: `README.md`
- Modify: `docs/learning-path.md`
- Create: `docs/reference/index.md`
- Create: `docs/advanced/index.md`
- Modify: `tests/test_project_contract.py`

**Interfaces:**
- Chinese README answers audience, Agent-loop failure, 45-minute promise, first command, expected Trace, and framework mapping before catalogues.
- Reference and advanced indexes link to existing architecture, metrics, numeric experiments, model adapter, and local tool documents without moving or deleting them.

- [ ] **Step 1: Write failing public-entry tests**

```python
def test_chinese_readme_explains_the_agent_loop_failure_and_first_course_step() -> None:
    readme = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    assert "已会 Python" in readme
    assert "45 分钟" in readme
    assert "为什么循环没有改进" in readme
    assert "course/01-baseline.md" in readme
    assert "experiments/code_repair/baseline.py" in readme
```

- [ ] **Step 2: Run red verification**

Run: `python -m pytest tests/test_project_contract.py -q`

Expected: FAIL because course-first commitments and indexes are absent.

- [ ] **Step 3: Rewrite entry documents and add indexes**

Place the code-repair failure and 45-minute promise before installation in the Chinese README. Link in order to `course/01-baseline.md`, the baseline command, subsequent lessons, reference index, and advanced index. Keep the English README concise and accurate about Chinese-first course materials. Turn `docs/learning-path.md` into a route map: course first, numeric mechanism references second, reference and advanced indexes last.

- [ ] **Step 4: Run green verification**

Run: `python -m pytest tests/test_project_contract.py tests/test_course_contract.py -q`

Run: `python scripts/check_docs.py`

Expected: PASS; the public entry reaches the first course activity without a long unprioritized catalogue.

- [ ] **Step 5: Commit**

```powershell
git add README.md README.zh-CN.md docs tests/test_project_contract.py
git commit -m "docs: make code repair course the public entry"
```

### Task 5: Protect the learning contract and release path

**Files:**
- Modify: `tests/test_docs_integrity.py`
- Modify: `tests/test_experiments.py`
- Modify: `docs/release-checklist.md`

**Interfaces:**
- Every course module is an offline, replayable `run() -> LoopTrace`.
- Documentation and release checks include all course commands and indexes.

- [ ] **Step 1: Write the failing end-to-end test**

```python
def test_code_repair_experiments_are_replayable_loop_runs() -> None:
    for module_name in ("baseline", "evaluator_signal", "feedback_strategy", "stopping_policy"):
        trace = importlib.import_module(f"experiments.code_repair.{module_name}").run()
        assert trace.final_state is not None
        assert trace.events[-1].phase == "STOP"
        assert any(event.phase == "EVALUATE" for event in trace.events)
```

- [ ] **Step 2: Run red verification**

Run: `python -m pytest tests/test_experiments.py -q`

Expected: FAIL until every module has the `run()` contract.

- [ ] **Step 3: Extend release and documentation checks**

Add all four course commands and `python scripts/check_docs.py` to the release checklist. Extend documentation tests for course and index files. Ensure every README command runs from repository root.

- [ ] **Step 4: Run complete verification**

Run: `python -m pytest -q`

Run: `python scripts/check_docs.py`

Run: `python -m build --wheel`

Run: `python experiments/code_repair/baseline.py`

Run: `python experiments/code_repair/evaluator_signal.py`

Run: `python experiments/code_repair/feedback_strategy.py`

Run: `python experiments/code_repair/stopping_policy.py`

Expected: all tests, documentation checks, build, and deterministic course commands pass.

- [ ] **Step 5: Commit**

```powershell
git add docs tests
git commit -m "test: protect Loop Engineering course contract"
```
