# Controlled Local Tool Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a diagnostic-only local subprocess adapter that can be used as an existing loop Action without changing Trace or Artifact contracts.

**Architecture:** `LocalToolAdapter` owns an immutable construction-time allowlist and executes only fixed argument vectors with `subprocess.run(..., shell=False)`. `ToolAction` converts one registered, parameterless decision into the existing `ActionResult`, allowing the unchanged runner to record outcomes and persist artifacts. A single Python-version experiment is the only example that starts a local process.

**Tech Stack:** Python 3.11+, standard library (`dataclasses`, `pathlib`, `subprocess`, `time`), pytest.

## Global Constraints

- Permit only explicitly registered, side-effect-free diagnostic commands.
- Every executable and working directory must be an absolute path; the directory must already exist.
- Commands use only the registered fixed argv with `shell=False`, `capture_output=True`, `text=True`, `check=False`, and the registered positive timeout.
- `Decision.parameters` must be exactly `{}`; no parameter, environment, or shell input may become command input.
- Do not register tools by default and do not make the CLI or existing experiments execute tools.
- Bound stdout and stderr independently to exactly `output_limit` characters; default `output_limit` is 1000.
- Non-zero exits and timeouts become failed `ActionResult` values; invalid registration or selection raises `ToolAdapterError`.
- Existing ACT payload remains exactly `{"success": result.success, "cost": result.cost}` and must not contain output.

---

## File Structure

- Create: `loop_engineering/tool_adapters.py` — registry validation, fixed subprocess execution, and bounded result records.
- Create: `loop_engineering/tool_action.py` — adapter-to-`ActionResult` bridge.
- Create: `tests/test_tool_adapters.py` — adapter contract and safety-boundary tests.
- Create: `tests/test_tool_action.py` — decision validation and runner/Artifact integration tests.
- Create: `experiments/local_tool_adapter.py` — replayable Python-version teaching experiment.
- Create: `tests/test_local_tool_adapter.py` — experiment report and Artifact contract test.
- Create: `docs/local-tool-adapter.md` — diagnostic-only registration, observability, and unsupported-capability guide.
- Modify: `docs/experiments.md` — add the experiment command and description.
- Modify: `README.md` — add the English learning-path entry.
- Modify: `README.zh-CN.md` — add the Chinese guide link and learning-path entry.
- Modify: `docs/architecture.md` — describe the explicit local-tool Action boundary.
- Modify: `docs/superpowers/sdd/progress.md` — record completion and verified test count.

### Task 1: Fixed local tool registry and execution boundary

**Files:**
- Create: `loop_engineering/tool_adapters.py`
- Create: `tests/test_tool_adapters.py`

**Interfaces:**
- Produces: `ToolAdapterError(ValueError)`, `ToolDefinition`, `ToolExecution`, and `LocalToolAdapter(definitions, output_limit=1000)`.
- Produces: `LocalToolAdapter.execute(name: str) -> ToolExecution` for `ToolAction` in Task 2.

- [ ] **Step 1: Write failing adapter-contract tests**

```python
def test_adapter_uses_registered_fixed_argv_and_bounded_output(monkeypatch, tmp_path):
    definition = ToolDefinition(
        name="python-version",
        executable=str(Path(sys.executable).resolve()),
        arguments=("--version",),
        working_directory=str(tmp_path.resolve()),
        timeout_seconds=2.0,
    )
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="x" * 6, stderr="y" * 6)

    monkeypatch.setattr("loop_engineering.tool_adapters.subprocess.run", fake_run)
    result = LocalToolAdapter([definition], output_limit=5).execute("python-version")

    assert calls == [
        ([str(Path(sys.executable).resolve()), "--version"], {
            "cwd": str(tmp_path.resolve()), "shell": False, "capture_output": True,
            "text": True, "timeout": 2.0, "check": False,
        })
    ]
    assert result.success is True
    assert result.stdout == "x" * 5
    assert result.stderr == "y" * 5
```

Add focused tests that assert `ToolAdapterError` for an unknown name, duplicate or blank names, relative executable or working-directory paths, a missing/non-directory working directory, and non-positive timeout or output limit. Add fixed-command tests for a non-zero exit and a mocked `subprocess.TimeoutExpired` result with `success is False` and `exit_code is None`.

- [ ] **Step 2: Run the adapter tests to verify they fail**

Run: `python -m pytest tests/test_tool_adapters.py -v`

Expected: FAIL during collection because `loop_engineering.tool_adapters` does not exist.

- [ ] **Step 3: Implement the validated fixed-command adapter**

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    executable: str
    arguments: tuple[str, ...]
    working_directory: str
    timeout_seconds: float

@dataclass(frozen=True)
class ToolExecution:
    success: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float

class LocalToolAdapter:
    def execute(self, name: str) -> ToolExecution:
        definition = self._definitions.get(name)
        if definition is None:
            raise ToolAdapterError(f"Unregistered tool: {name}")
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [definition.executable, *definition.arguments],
                cwd=definition.working_directory,
                shell=False,
                capture_output=True,
                text=True,
                timeout=definition.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return ToolExecution(False, None, self._bound(error.stdout), self._bound(error.stderr), time.perf_counter() - started)
        return ToolExecution(completed.returncode == 0, completed.returncode, self._bound(completed.stdout), self._bound(completed.stderr), time.perf_counter() - started)
```

Normalize timeout byte output to text before bounding it. Validate all definitions in `__init__`, store them in a private name-to-definition mapping, and never expose an API that accepts extra command arguments.

- [ ] **Step 4: Run the adapter tests to verify they pass**

Run: `python -m pytest tests/test_tool_adapters.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the adapter boundary**

```bash
git add loop_engineering/tool_adapters.py tests/test_tool_adapters.py
git commit -m "feat: add controlled local tool adapter"
```

### Task 2: ToolAction mapping and unchanged runtime observability

**Files:**
- Create: `loop_engineering/tool_action.py`
- Create: `tests/test_tool_action.py`

**Interfaces:**
- Consumes: `LocalToolAdapter.execute(name) -> ToolExecution` from Task 1 and `ActionResult` from `loop_engineering/actions.py`.
- Produces: `ToolAction(adapter).apply(state: LoopState, decision: Decision) -> ActionResult`.

- [ ] **Step 1: Write failing ToolAction and loop-integration tests**

```python
def test_tool_action_rejects_dynamic_decision_parameters(tmp_path):
    action = ToolAction(LocalToolAdapter([python_version_definition(tmp_path)]))

    with pytest.raises(ToolAdapterError, match="parameters"):
        action.apply(LoopState(0, 0.0, 0.0), Decision("python-version", {"extra": 1.0}))

class FixedDecisionPolicy(Policy):
    def __init__(self, decision):
        self.decision = decision

    def decide(self, state, feedback, recent_events=None):
        return self.decision

def test_tool_action_keeps_trace_and_artifact_output_free(tmp_path):
    trace = LoopRunner(
        FixedDecisionPolicy(Decision("python-version", {})),
        ToolAction(LocalToolAdapter([python_version_definition(tmp_path)])),
        GoalEvaluator(0.0),
        [SuccessReached(), MaxSteps(1)],
    ).run(LoopState(0, 0.0, 0.0))

    assert trace.events[2].payload.keys() == {"success", "cost"}
    artifact = save_run_artifact(tmp_path / "artifact.json", trace)
    assert "Python" not in artifact.read_text(encoding="utf-8")
```

Add a non-zero and timeout mapping test that verifies unchanged numeric state, `success is False`, and a non-negative `cost`. Add an unknown-name test asserting `ToolAdapterError` propagates before loop recording.

- [ ] **Step 2: Run the ToolAction tests to verify they fail**

Run: `python -m pytest tests/test_tool_action.py -v`

Expected: FAIL during collection because `loop_engineering.tool_action` does not exist.

- [ ] **Step 3: Implement the Action bridge**

```python
class ToolAction(Action):
    def __init__(self, adapter: LocalToolAdapter) -> None:
        self.adapter = adapter

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if decision.parameters != {}:
            raise ToolAdapterError("Tool decisions must not include parameters")
        execution = self.adapter.execute(decision.name)
        return ActionResult(
            state=state.with_value(state.value),
            success=execution.success,
            cost=execution.duration_seconds,
        )
```

Do not change `LoopRunner`, `ActionResult`, Artifact serialization, or ACT event construction. The action is responsible only for validation and status/cost mapping.

- [ ] **Step 4: Run the ToolAction tests to verify they pass**

Run: `python -m pytest tests/test_tool_action.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the Action bridge**

```bash
git add loop_engineering/tool_action.py tests/test_tool_action.py
git commit -m "feat: map local tools into loop actions"
```

### Task 3: Safe teaching experiment and learner documentation

**Files:**
- Create: `experiments/local_tool_adapter.py`
- Create: `tests/test_local_tool_adapter.py`
- Create: `docs/local-tool-adapter.md`
- Modify: `docs/experiments.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/architecture.md`
- Modify: `docs/superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: `ToolDefinition`, `LocalToolAdapter`, `ToolAction`, `LoopRunner`, and `save_run_artifact`.
- Produces: `run_local_tool_adapter_demo(output_dir: str | Path = ".loop/runs/local-tool-adapter") -> dict[str, object]`.

- [ ] **Step 1: Write the failing replayable-demo test**

```python
def test_local_tool_adapter_demo_is_replayable_and_keeps_output_out_of_artifact(tmp_path):
    report = run_local_tool_adapter_demo(tmp_path)

    assert report["status"] == "SUCCEEDED"
    assert report["tool_name"] == "python-version"
    assert report["exit_code"] == 0
    assert report["duration_seconds"] >= 0.0
    assert "Python" in report["output"]
    trace, metrics = load_run_artifact(Path(report["artifact_path"]))
    assert metrics.success is True
    assert trace.events[2].payload.keys() == {"success", "cost"}
    assert report["output"] not in Path(report["artifact_path"]).read_text(encoding="utf-8")
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == report
```

- [ ] **Step 2: Run the demo test to verify it fails**

Run: `python -m pytest tests/test_local_tool_adapter.py -v`

Expected: FAIL during collection because `experiments.local_tool_adapter` does not exist.

- [ ] **Step 3: Implement the explicit Python-version demo**

```python
definition = ToolDefinition(
    name="python-version",
    executable=str(Path(sys.executable).resolve()),
    arguments=("--version",),
    working_directory=str(root),
    timeout_seconds=2.0,
)
```

Resolve and create only the caller-provided output directory. Define a small local `PythonVersionPolicy(Policy)` that always returns `Decision("python-version", {})`, then run it through `ToolAction`, `GoalEvaluator(0.0)`, `SuccessReached()`, and `MaxSteps(1)`. Write `artifact.json` and a JSON `report.json`; return a report with artifact path, status, tool name, exit code, duration, and combined bounded stdout/stderr output. The command has no project-file writes and no network access.

- [ ] **Step 4: Document the boundary and link the experiment**

Write `docs/local-tool-adapter.md` in Chinese. It must explain explicit registration, absolute executable and directory, fixed argv, `shell=False`, parameter rejection, output truncation, timeout/non-zero behavior, and why output is intentionally absent from Trace/Artifact. List unsupported capabilities: arbitrary shell, dynamic arguments, environment injection, project-file modification, network tools, chains, and implicit CLI execution.

Add `python experiments/local_tool_adapter.py` and a short diagnostic-only description to `docs/experiments.md`. Add guide links and learning-path entries to both READMEs. Add the explicit tool-adapter Action boundary and default-no-tools guarantee to `docs/architecture.md`.

- [ ] **Step 5: Run focused and complete verification**

Run: `python -m pytest tests/test_tool_adapters.py tests/test_tool_action.py tests/test_local_tool_adapter.py -v`

Expected: PASS.

Run: `python experiments/local_tool_adapter.py`

Expected: JSON report with `python-version`, a successful status, bounded output, and a replayable artifact under `.loop/runs/local-tool-adapter`.

Run: `python -m pytest -q`

Expected: PASS with the full project suite.

- [ ] **Step 6: Record verified status and commit the teaching surface**

Update `docs/superpowers/sdd/progress.md` with the exact full-suite test count reported by the final command, then run the full suite once more after that documentation edit.

```bash
git add experiments/local_tool_adapter.py tests/test_local_tool_adapter.py docs/local-tool-adapter.md docs/experiments.md README.md README.zh-CN.md docs/architecture.md docs/superpowers/sdd/progress.md
git commit -m "docs: add local tool adapter learning experiment"
```

## Self-Review

- Spec coverage: Task 1 covers allowlisting, absolute-path validation, fixed argv, shell disabling, bounded streams, non-zero exits, and timeouts. Task 2 covers decision validation, state preservation, ActionResult mapping, and unchanged ACT/Artifact behavior. Task 3 covers the diagnostic Python-version experiment, no-default-tool boundary, documentation, and full-suite verification.
- Placeholder scan: no deferred implementation markers or unspecified validation steps remain.
- Type consistency: Task 1 defines `ToolDefinition`, `ToolExecution`, `LocalToolAdapter.execute`, and `ToolAdapterError`; Tasks 2 and 3 consume those exact names.
