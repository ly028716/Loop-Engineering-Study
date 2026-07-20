# Task 4 Report

## Status

Implemented the observable loop runner and explicit stopping conditions. The
scope is limited to Task 4; no memory, metrics, CLI, experiments, or external
model integrations were added. No Git commit was created.

## Files

- `loop_engineering/stopping.py`: `StopDecision`, the `StopCondition` contract,
  `SuccessReached`, and validated `MaxSteps`.
- `loop_engineering/runner.py`: deterministic `LoopRunner` phase machine with
  a configurable safety iteration limit.
- `tests/test_stopping.py`: success, continued-running, max-step, and invalid
  max-step coverage.
- `tests/test_runner.py`: successful completion, maximum-step stop, phase
  order, stop reasons, feedback forwarding, and safety-stop coverage.

## Runtime behavior

Each iteration records `OBSERVE`, `DECIDE`, `ACT`, `EVALUATE`, and `FEEDBACK`
in that order. The runner converts the current evaluation into feedback for the
following policy decision. It then checks configured stopping conditions in
their supplied order. A matching condition records a `STOP` event and assigns
its status and reason to the final state. If no condition matches before the
configured safety limit, the runner records a `STOPPED` event with the safety
limit reason.

## Test results

Bundled Python 3.11 was used:

```text
C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests/test_stopping.py tests/test_runner.py -q
8 passed in 0.06s

C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe -m pytest -q
21 passed in 0.86s
```

## Concerns

The workspace sandbox denies direct execution of the bundled interpreter, so
tests required the approved unsandboxed execution path. The repository itself
is otherwise green.
