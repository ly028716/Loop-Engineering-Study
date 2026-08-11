# Loop Engineering Study

> An executable learning laboratory for Loop Engineering.

Loop Engineering Study is an independent, local-first Python project for
studying how observable, repeatable improvement loops are designed and
evaluated. It is a learning runtime and experiment collection, not an agent
platform or production harness.

## Documentation language

The detailed learning materials are Chinese-first. This English README is a
project overview; use the [Chinese README](README.zh-CN.md) and the
[learning path](docs/learning-path.md) for the complete guided curriculum.

The baseline is deterministic and requires no API key, database, model service,
or web framework. Each run makes the loop visible:

```text
OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK → STOP
```

## What is implemented

- A small `LoopRunner` with explicit state, policy, action, evaluator, memory,
  metrics, and stopping-condition boundaries.
- Structured event traces for every loop round.
- JSON artifacts containing `events`, `final_state`, and `metrics`.
- Deterministic success, retry, failure, and stop behavior.
- A CLI plus three executable experiments: `basic_loop`, `retry_loop`, and
  `repair_loop`.
- A pytest suite covering the runtime and packaging contract.

The project deliberately starts with deterministic behavior. External models or
services are future experiment inputs, not hidden dependencies of the baseline.

## Quick start

Requires Python 3.11 or newer:

```powershell
python -m pip install -e ".[dev]"
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json
Get-Content -Raw .loop/runs/demo.json
```

The CLI prints a JSON summary and writes a complete replayable artifact. Run the
three learning experiments in order:

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
```

## 30-minute beginner route

1. Run the CLI command above and open `.loop/runs/demo.json`.
2. Run `basic_loop`, then `retry_loop`, then `repair_loop` to see success,
   feedback-driven retry, and a bounded stop caused by evaluator disagreement.
3. Read [Loop concepts](docs/concepts.md) and follow the Chinese-first
   [learning path](docs/learning-path.md) before changing one loop component.

### Trace preview

Every round makes its evidence explicit. A typical deterministic run has this
shape:

```text
OBSERVE value=0, goal=3
DECIDE increment(amount=1)
ACT success=True, value=1
EVALUATE score=0.33
FEEDBACK continue
...
STOP status=SUCCEEDED, reason="Evaluation reported success"
```

The saved artifact contains the ordered events, final state, and metrics, so it
can be inspected without executing actions again.

## Advanced study

After the beginner route, use the [experiment catalogue](docs/experiments.md)
to choose one focused extension at a time:

- Feedback, memory, convergence, and failure behavior:
  [feedback strategies](docs/feedback-strategies.md),
  [memory capacity](docs/memory-capacity.md), and
  [convergence and stopping](docs/convergence-stopping.md).
- Evaluation and diagnosis: [benchmark suite](docs/benchmark-suite.md),
  [trace diagnostics](docs/trace-diagnostics.md), and
  [artifact replay](docs/replay.md).
- Explicit integration boundaries: [external HTTP models](docs/external-model-adapter.md)
  and [controlled local tools](docs/local-tool-adapter.md).
- Reference material: [architecture](docs/architecture.md),
  [metrics](docs/metrics.md), and [theory notes](theory/).

## Development

```powershell
python -m pytest -q
python -m build --wheel
```

CI runs the Python test-and-build matrix first, then a separate Python 3.11
semantic gate that uploads `semantic-gate-evidence` for diagnosis.

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. CI runs
the same test and wheel-build checks on supported Python versions.

Use the [release checklist](docs/release-checklist.md) when preparing a public
GitHub release.

## Scope

This repository is intentionally an independent study of loop engineering. It
does not claim to be a general-purpose autonomous-agent framework, an LLM
orchestration system, or a production reliability solution. New capabilities
should preserve observable traces, deterministic tests where possible, and
explicit stopping conditions.

## License

Released under the [MIT License](LICENSE).
