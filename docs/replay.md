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

## Replay and compare from the CLI

```powershell
python -m loop_engineering.cli replay .loop/runs/demo.json
python -m loop_engineering.cli compare .loop/runs/baseline.json .loop/runs/repaired.json
```

`replay` prints the complete ordered events, final state, and metrics from one
Artifact. `compare` prints whether two Artifacts are identical and, when they
are not, the first observable event, final-state, or metric difference. Both
commands are read-only: they load evidence and never execute stored actions.

## What replay means here

The current implementation supports inspection and deterministic restoration of
the trace and metrics. It does not re-execute actions, reproduce external side
effects, or claim event-sourcing semantics. An artifact is evidence of a run,
not permission to run the action again.

The generic CLI `compare` command provides a read-only, first-difference
comparison for any two compatible Artifacts. The scenario-specific
`experiments/trace_diff_analysis.py` report applies the same semantics to
diagnosis-repair pairs; see [Trace difference analysis](trace-diff-analysis.md).

Future experiments can still grow into policy diffs or counterfactual
evaluation, while preserving the current read-only loading behavior.
