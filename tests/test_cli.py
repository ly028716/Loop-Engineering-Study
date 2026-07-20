import json
import subprocess
import sys
from pathlib import Path

from loop_engineering.artifacts import load_run_artifact
from loop_engineering.metrics import MetricReport


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "loop_engineering.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_run_writes_replayable_trace_and_json_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "run.json"

    result = run_cli(
        "run",
        "--goal",
        "3",
        "--max-steps",
        "10",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary == {
        "status": "SUCCEEDED",
        "steps": 3,
        "final_value": 3.0,
        "score": 1.0,
        "trace_path": str(output_path.resolve()),
    }

    artifact = json.loads(output_path.read_text(encoding="utf-8"))
    assert artifact["final_state"] == {
        "step": 3,
        "value": 3.0,
        "goal": 3.0,
        "status": "SUCCEEDED",
        "metadata": {},
    }
    assert artifact["metrics"] == {
        "steps": 3,
        "final_score": 1.0,
        "success": True,
        "cost": 3.0,
        "average_step_gain": 0.33333333333333337,
    }
    assert [event["phase"] for event in artifact["events"]] == [
        "OBSERVE",
        "DECIDE",
        "ACT",
        "EVALUATE",
        "FEEDBACK",
        "OBSERVE",
        "DECIDE",
        "ACT",
        "EVALUATE",
        "FEEDBACK",
        "OBSERVE",
        "DECIDE",
        "ACT",
        "EVALUATE",
        "FEEDBACK",
        "STOP",
    ]
    loaded_trace, loaded_metrics = load_run_artifact(output_path)
    assert loaded_trace.final_state is not None
    assert loaded_trace.final_state.status == "SUCCEEDED"
    assert loaded_metrics == MetricReport(
        steps=3,
        final_score=1.0,
        success=True,
        cost=3.0,
        average_step_gain=0.33333333333333337,
    )


def test_cli_run_rejects_max_steps_below_one(tmp_path: Path) -> None:
    result = run_cli(
        "run",
        "--goal",
        "3",
        "--max-steps",
        "0",
        "--output",
        str(tmp_path / "run.json"),
    )

    assert result.returncode != 0
    assert "--max-steps must be at least 1" in result.stderr
