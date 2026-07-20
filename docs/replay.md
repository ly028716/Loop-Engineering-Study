# Replayable artifacts

Each CLI or experiment run writes a UTF-8 JSON artifact. The artifact contains
the complete run boundary:

```json
{
  "events": [],
  "final_state": {},
  "metrics": {}
}
```

`events` preserves the ordered lifecycle records. `final_state` captures the
last state without requiring another run. `metrics` stores the report that was
derived when the run finished.

## Load an artifact

```python
from loop_engineering.artifacts import load_run_artifact

trace, report = load_run_artifact(".loop/runs/demo.json")
print(report.status, report.steps)
print(len(trace.events))
```

## What replay means here

The current implementation supports inspection and deterministic restoration of
the trace and metrics. It does not re-execute actions, reproduce external side
effects, or claim event-sourcing semantics. An artifact is evidence of a run,
not permission to run the action again.

For future experiments, replay can grow into step-by-step comparison, policy
diffs, or counterfactual evaluation. Those features should preserve the current
read-only loading behavior.
