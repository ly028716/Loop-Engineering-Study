# Metrics

Metrics are derived from a completed `LoopTrace` by
`MetricReport.from_trace(trace)`. They describe what happened; they do not
replace the event trace.

| Metric | Meaning |
| --- | --- |
| `steps` | Number of loop rounds represented by the trace. |
| `final_value` | Final numeric value in the terminal state, when present. |
| `score` | Final evaluator score, normalized to the runtime's current scale. |
| `status` | Terminal status such as `SUCCEEDED` or `STOPPED`. |
| `stop_reason` | Explicit reason recorded by the stopping condition. |
| `improvement` | Difference between the initial and final value where available. |

## How to read the metrics

Use `status` and `stop_reason` to understand termination, `steps` to understand
loop cost, and `score`/`improvement` to understand outcome. Always inspect the
events when a metric looks surprising: a high final value does not prove that
the evaluator was correct, as demonstrated by `repair_loop`.

Metrics are intentionally small and deterministic in this baseline. Future
experiments can add latency, retry count, evaluator disagreement, or cost, but
each new metric should have a written definition and a test for its boundary
cases.
