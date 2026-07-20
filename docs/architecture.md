# Architecture

The runtime keeps the learning surface small and explicit. A run is a sequence
of bounded rounds:

```text
LoopState
   ↓
OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK
                                      ↓
                               Memory / Metrics
                                      ↓
                              Stopping decision
```

## Components

- `LoopState` is the current mutable state and goal context.
- A policy turns the observed state into one bounded decision.
- An action applies that decision and returns the next state.
- An evaluator compares the result with the goal and produces feedback.
- Memory stores selected observations across rounds.
- Metrics derive a compact report from the completed trace.
- A stopping condition decides whether the loop succeeds, stops, or continues.
- `LoopTrace` is the observable contract connecting these components.

The runner coordinates these components but does not hide their decisions. This
separation makes it possible to replace one component in an experiment while
keeping the trace and tests stable.

## Run lifecycle

For each round, the runner records `OBSERVE`, `DECIDE`, `ACT`, `EVALUATE`, and
`FEEDBACK`. It then checks stopping conditions. A terminal run records a final
`STOP` event and can be persisted through `save_run_artifact()`.

The CLI and direct experiment scripts use the same runtime boundary. They differ
only in how policies, actions, evaluators, and fault conditions are configured.

## Design boundaries

The baseline is intentionally local and deterministic. There is no network
client, model adapter, database, scheduler, or hidden global state. These may be
added as later study experiments, but they should enter through explicit
component interfaces and preserve observability.
