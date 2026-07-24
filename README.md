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
4. [Feedback strategy comparison](docs/feedback-strategies.md)
5. [Memory capacity comparison](docs/memory-capacity.md)
6. [Convergence and stopping](docs/convergence-stopping.md)
7. [Failure modes and recovery](docs/failure-modes.md)
8. [Adaptive strategy and budget allocation](docs/adaptive-strategy.md)
9. [Benchmark suite and ranking](docs/benchmark-suite.md)
10. [Multi-objective evaluation](docs/multi-objective-evaluation.md)
11. [Parameter sensitivity analysis](docs/sensitivity-analysis.md)
12. [Trace diagnostics](docs/trace-diagnostics.md)
13. [Diagnosis-driven repair loop](docs/diagnosis-repair-loop.md)
14. [Multi-repair selection](docs/multi-repair-selection.md)
15. [Stochastic robustness experiment](docs/stochastic-robustness.md)
16. [Trace difference analysis](docs/trace-diff-analysis.md)
17. [Artifact replay and comparison](docs/replay.md)
18. [External HTTP model adapter](docs/external-model-adapter.md)
19. [Semantic regression gate](docs/regression-gate.md)
20. [Architecture](docs/architecture.md)
21. [Metrics](docs/metrics.md)
22. [Theory notes](theory/)

## Development

```powershell
python -m pytest -q
python -m build --wheel
```

CI runs the Python test-and-build matrix first, then a separate Python 3.11
semantic gate that uploads `semantic-gate-evidence` for diagnosis.

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
