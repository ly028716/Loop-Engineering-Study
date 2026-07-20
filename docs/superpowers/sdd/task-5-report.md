# Task 5 Report

## Status

Implemented bounded working memory, trace-derived metrics, and runner memory
integration. The scope is limited to Task 5: no CLI or experiments were added,
and no Git commit was created.

## Files

- `loop_engineering/memory.py`: bounded `WorkingMemory` backed by
  `deque(maxlen=capacity)` with capacity validation and chronological recent
  event retrieval.
- `loop_engineering/metrics.py`: immutable `MetricReport` derived from a
  `LoopTrace` without modifying it.
- `loop_engineering/policies.py`: optional `recent_events` parameter added to
  the policy contract and `IncrementPolicy` while retaining two-argument use.
- `loop_engineering/runner.py`: records every emitted event in working memory
  and supplies recent events to policies that accept a third argument.
- `tests/test_memory.py`: capacity, recent-tail, and invalid-capacity coverage.
- `tests/test_metrics.py`: steps, final score, success, cost, average gain, and
  non-mutation coverage.
- `tests/test_runner.py`: memory persistence and compatible policy integration
  coverage.

## Test results

The shell had no `python` command. The available Python 3.11 interpreter was
used instead:

```text
C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python311\\python.exe -m pytest tests/test_memory.py tests/test_metrics.py tests/test_runner.py -q
.........                                                                [100%]
9 passed in 0.05s
```

Complete-suite verification:

```text
C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python311\\python.exe -m pytest -q
..........................                                               [100%]
26 passed in 0.92s
```

## Concerns

`MetricReport.average_step_gain` is the mean change between successive
`EVALUATE` scores. A trace containing zero or one score reports `0.0`, because
there is no score-to-score gain to average.
