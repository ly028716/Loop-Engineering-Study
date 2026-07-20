# Loop Engineering Study

> An executable learning laboratory for Loop Engineering.

Loop Engineering Study is an independent, local-first Python project for
studying how observable, repeatable improvement loops are designed and
evaluated. It is a learning runtime and experiment collection, not an agent
platform or production harness.

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

## Learning path

Start with the conceptual model, then inspect one complete loop, feedback,
memory, convergence, and stopping behavior:

1. [Loop concepts](docs/concepts.md)
2. [Learning path](docs/learning-path.md)
3. [Experiments](docs/experiments.md)
4. [Architecture](docs/architecture.md)
5. [Metrics](docs/metrics.md)
6. [Replayable artifacts](docs/replay.md)
7. [Theory notes](theory/)

## Development

```powershell
python -m pytest -q
python -m build --wheel
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. CI runs
the same test and wheel-build checks on supported Python versions.

## Scope

This repository is intentionally an independent study of loop engineering. It
does not claim to be a general-purpose autonomous-agent framework, an LLM
orchestration system, or a production reliability solution. New capabilities
should preserve observable traces, deterministic tests where possible, and
explicit stopping conditions.

## License

Released under the [MIT License](LICENSE).
