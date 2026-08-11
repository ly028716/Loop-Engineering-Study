# Loop Engineering Study

An executable, local-first course for Python developers learning how AI/Agent loops improve through decision, action, evaluation, feedback, and stopping policies.

The Chinese-first [course README](README.zh-CN.md) is the primary entry point. In about 45 minutes, its deterministic code-repair case lets you inspect a failing loop, run three controlled experiments, and verify one improvement with before/after artifacts. No API key, model service, or network is required.

## Start here

```powershell
python -m pip install -e ".[dev]"
python experiments/code_repair/baseline.py
```

Then follow the three lessons:

1. [Baseline](course/01-baseline.md)
2. [Read the trace](course/02-read-the-trace.md)
3. [Improve the loop](course/03-improve-the-loop.md)

The small reusable framework exposes `Policy`, `Action`, `Evaluator`, `StopPolicy`, structured traces, and JSON artifacts. Follow-up material is organized in the [reference index](docs/reference/index.md) and [advanced index](docs/advanced/index.md).

## Development

```powershell
python -m pytest -q
python scripts/check_docs.py
python -m build --wheel
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [release checklist](docs/release-checklist.md). Released under the [MIT License](LICENSE).
