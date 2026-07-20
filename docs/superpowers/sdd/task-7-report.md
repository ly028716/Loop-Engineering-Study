# Task 7 Report

## Status

Implemented the three deterministic, local-only loop experiments and their
learning documentation. Each experiment exposes `run() -> LoopTrace`, records
a final `STOP` event through `LoopRunner`, and can be run with bundled Python
using `-m experiments.<module>`. No CLI or public API changes were needed, and
no Git commit was created.

## Files

- `experiments/__init__.py`: package marker for module execution.
- `experiments/basic_loop.py`: stable bounded numeric approach to a target.
- `experiments/retry_loop.py`: one injected action failure and
  feedback-driven larger retry action.
- `experiments/repair_loop.py`: successful action/target state rejected by a
  deliberately faulty evaluator.
- `tests/test_experiments.py`: parameterized module-name contract test for
  `LoopTrace`, final state, events, and final `STOP` phase.
- `theory/loop-models.md`: model and phase-machine explanation.
- `theory/feedback-systems.md`: feedback behavior linked to retry experiment.
- `theory/state-and-memory.md`: distinction between state, trace, memory, and
  feedback.
- `theory/convergence.md`: score/error convergence and faulty-evaluation
  contrast.
- `theory/stopping-conditions.md`: success, maximum-step, and safety stops.
- `docs/experiments.md`: runnable order and output description.
- `examples/README.md`: purpose of each learning case.

## Test Results

The sandbox denied direct execution of the bundled interpreter, so the
approved execution path used the existing Python 3.11 installation.

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
...............................                                          [100%]
31 passed in 1.82s
```

Basic-loop smoke output:

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m experiments.basic_loop
rounds: 3
final state: LoopState(step=3, value=5.0, goal=5.0, status='SUCCEEDED', metadata={})
final score: 1.0
stop reason: Evaluation reported success
scores: [0.25, 0.5, 1.0]
```

## Concerns

The workspace exposes a `.git` directory but `git` reports that the directory
is not a repository, so no repository status was available. The system Python
execution path was sandbox-denied and required the approved existing Python
3.11 path. The experiments make no network or external-service calls.
