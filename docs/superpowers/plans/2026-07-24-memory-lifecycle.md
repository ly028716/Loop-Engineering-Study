# Memory Lifecycle Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Isolate WorkingMemory to each LoopRunner run so every saved Trace and Artifact fully explains the policy history used in that run.

**Architecture:** Add a small clear method to WorkingMemory and call it at the start of LoopRunner.run before any event is recorded. Tests prove memory-window clearing and repeated-run isolation; documentation defines memory as a bounded per-run event window.

**Tech Stack:** Python 3.11, standard library collections, pytest, Markdown.

## Global Constraints

- Preserve WorkingMemory capacity and object identity when clearing.
- Clear memory only at the start of LoopRunner.run, never between rounds.
- Do not modify Artifact JSON format, CLI behavior, experiment APIs, or Policy signatures.
- Existing same-run memory behavior must remain unchanged.
- Follow TDD and commit each independently testable task.

---

## Task 1: Add WorkingMemory clearing and protect the lifecycle contract

**Files:**

- Modify: tests/test_memory.py
- Modify: tests/test_runner.py
- Modify: loop_engineering/memory.py
- Modify: loop_engineering/runner.py

**Interfaces:**

- Produces: WorkingMemory.clear() returning None.
- Consumes: LoopRunner.run clears self.memory before creating a new Trace.

- [ ] **Step 1: Write failing unit and runner isolation tests**

Append to tests/test_memory.py:

~~~python
def test_working_memory_clear_forgets_events_and_keeps_capacity() -> None:
    from loop_engineering.memory import WorkingMemory

    memory = WorkingMemory(capacity=2)
    memory.add(event(1))
    memory.add(event(2))

    memory.clear()

    assert memory.capacity == 2
    assert memory.recent(10) == []
    memory.add(event(3))
    assert memory.recent(10) == [event(3)]
~~~

Append to tests/test_runner.py:

~~~python
def test_runner_clears_memory_before_each_new_run() -> None:
    policy = MemoryRecordingPolicy()
    memory = WorkingMemory(capacity=20)
    runner = LoopRunner(
        policy=policy,
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[MaxSteps(1)],
        memory=memory,
    )

    first_trace = runner.run(LoopState(step=0, value=0.0, goal=5.0))
    second_trace = runner.run(LoopState(step=0, value=0.0, goal=5.0))

    assert [event.phase for event in policy.recent_events[0]] == ["OBSERVE"]
    assert [event.phase for event in policy.recent_events[1]] == [
        "OBSERVE", "DECIDE", "ACT", "EVALUATE", "FEEDBACK", "STOP", "OBSERVE"
    ]
    assert policy.recent_events[2] == [second_trace.events[0]]
    assert memory.recent(20) == second_trace.events
    assert first_trace.events != second_trace.events
~~~

- [ ] **Step 2: Verify RED**

Run: python -m pytest tests/test_memory.py tests/test_runner.py -q

Expected: failure because clear is absent and second-run policy history includes the first run.

- [ ] **Step 3: Add the minimal clear implementation**

In loop_engineering/memory.py, add:

~~~python
    def clear(self) -> None:
        """Forget all events while retaining the configured capacity."""

        self._events.clear()
~~~

At the beginning of LoopRunner.run in loop_engineering/runner.py, before constructing LoopTrace, add:

~~~python
        self.memory.clear()
~~~

- [ ] **Step 4: Verify GREEN**

Run: python -m pytest tests/test_memory.py tests/test_runner.py -q

Expected: all memory and runner tests pass; existing same-run context test remains green.

- [ ] **Step 5: Commit**

~~~powershell
git add loop_engineering/memory.py loop_engineering/runner.py tests/test_memory.py tests/test_runner.py
git commit -m "fix: isolate memory per loop run"
~~~

## Task 2: Document the per-run memory boundary and verify the project

**Files:**

- Modify: docs/memory-capacity.md
- Modify: docs/architecture.md
- Modify: docs/superpowers/sdd/progress.md

**Interfaces:**

- Consumes: per-run WorkingMemory contract from Task 1.
- Produces: documentation aligning Artifact replay expectations with memory scope.

- [ ] **Step 1: Update memory-capacity documentation**

After the opening explanation in docs/memory-capacity.md, add:

~~~markdown
WorkingMemory is reset at the start of every LoopRunner.run call. Its window
therefore contains only events from the current run; a saved Artifact contains
the same event history that was available to policies in that run. It is not
cross-run persistent memory.
~~~

- [ ] **Step 2: Update architecture documentation**

Replace the Memory component bullet in docs/architecture.md with:

~~~markdown
- Memory stores a bounded event window for the current run and is cleared before the next run begins.
~~~

After the Run lifecycle paragraph, add:

~~~markdown
A runner may be reused, but each run starts with an empty WorkingMemory.
This makes the resulting Trace and Artifact self-contained evidence for every
policy decision in that run.
~~~

- [ ] **Step 3: Run complete verification and update progress**

Run:

~~~powershell
python -m pytest -q
git diff --check
~~~

Expected: all tests pass and whitespace check has no output.

Append one progress entry recording per-run memory reset, self-contained Artifact decision context, and the exact final test count.

- [ ] **Step 4: Commit**

~~~powershell
git add docs/memory-capacity.md docs/architecture.md docs/superpowers/sdd/progress.md
git commit -m "docs: clarify memory lifecycle"
~~~

