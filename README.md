# Loop Engineering Study

This is an independent study project for Loop Engineering: designing observable,
repeatable improvement loops around a changing state and an explicit goal.
It is intentionally separate from any agent platform or production harness.
The baseline is deterministic and local-only: no API key, database, model
service, or web framework is required.

## Core loop

`OBSERVE → DECIDE → ACT → EVALUATE → FEEDBACK`

- **OBSERVE** records the current situation.
- **DECIDE** selects the next bounded move.
- **ACT** applies that move.
- **EVALUATE** checks the result against the goal.
- **FEEDBACK** turns the evaluation into input for the next round.

Every run ends with an explicit **STOP** event after a success or another
configured stopping condition.

## Install

Use Python 3.11 or newer. From the project root, install the package and its
pytest development dependency:

```powershell
python -m pip install -e ".[dev]"
```

No environment variables or credentials need to be configured.

## Run your first loop

Run the built-in deterministic loop from `0` to the goal `3`:

```powershell
python -m loop_engineering.cli run --goal 3 --max-steps 10 --output .loop/runs/demo.json
```

The command exits with a one-line JSON summary containing `status`, `steps`,
`final_value`, `score`, and the absolute `trace_path`. A successful run reports
`"status": "SUCCEEDED"` and writes the complete trace to
`.loop/runs/demo.json`.

## Inspect the trace

Windows PowerShell:

```powershell
Get-Content -Raw .loop/runs/demo.json
```

POSIX shell:

```sh
cat .loop/runs/demo.json
```

The `events` array records `OBSERVE`, `DECIDE`, `ACT`, `EVALUATE`, and
`FEEDBACK` for each round, followed by `STOP`. The same file also contains the
final state, so the run can be reviewed without rerunning it.

## Run the experiments

Three direct scripts demonstrate a stable loop, feedback-driven retry, and a
faulty evaluation:

```powershell
python experiments/basic_loop.py
python experiments/retry_loop.py
python experiments/repair_loop.py
```

Read [docs/experiments.md](docs/experiments.md) for the expected observations
and recommended order.

## Learning order

Follow the path from the loop concepts to a single deterministic round, then add
feedback, memory, convergence, and engineering cases. The detailed sequence is
in [docs/learning-path.md](docs/learning-path.md), with the current vocabulary in
[docs/concepts.md](docs/concepts.md).

The local baseline keeps policy, action, evaluator, memory, and stopping
conditions separate. A next experiment can replace one of those components
while preserving the same trace contract; external models should only be added
after the deterministic behavior is understood and tested.
