"""Contract tests for the runnable Task 7 experiments."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import subprocess
import sys

import pytest

from loop_engineering.artifacts import load_run_artifact
from loop_engineering.models import LoopTrace


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    [
        "experiments.basic_loop",
        "experiments.retry_loop",
        "experiments.repair_loop",
    ],
)
def test_experiment_run_returns_a_stopped_trace(module_name: str) -> None:
    module = import_module(module_name)

    trace = module.run()

    assert isinstance(trace, LoopTrace)
    assert trace.final_state is not None
    assert trace.events
    assert trace.events[-1].phase == "STOP"


@pytest.mark.parametrize(
    "script_name",
    ["basic_loop.py", "retry_loop.py", "repair_loop.py"],
)
def test_experiment_script_writes_loadable_artifact_and_prints_summary(
    script_name: str,
) -> None:
    artifact_path = PROJECT_ROOT / ".loop" / "runs" / f"{Path(script_name).stem}.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("stale artifact", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "experiments" / script_name)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "status=" in result.stdout
    assert "steps=" in result.stdout
    assert "score=" in result.stdout
    fields = dict(line.split("=", 1) for line in result.stdout.splitlines())
    assert fields["artifact_path"] == str(artifact_path.resolve())

    trace, metrics = load_run_artifact(artifact_path)
    assert trace.final_state is not None
    assert trace.final_state.status == fields["status"]
    assert metrics.steps == int(fields["steps"])
    assert metrics.final_score == float(fields["score"])


def test_experiment_package_import_does_not_change_sys_path() -> None:
    probe = "\n".join(
        [
            "import sys",
            "before = list(sys.path)",
            "import experiments.basic_loop",
            "assert sys.path == before, (before, sys.path)",
        ]
    )

    result = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
