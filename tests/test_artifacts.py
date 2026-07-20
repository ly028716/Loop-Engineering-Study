"""Round-trip contracts for complete run artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from loop_engineering.artifacts import load_run_artifact, save_run_artifact
from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopEvent, LoopState, LoopTrace


def test_run_artifact_round_trip_restores_trace_and_metrics(tmp_path: Path) -> None:
    trace = LoopTrace(
        events=[
            LoopEvent(step=1, phase="ACT", payload={"cost": 0.75, "message": "执行"}),
            LoopEvent(step=1, phase="EVALUATE", payload={"score": 0.25}),
            LoopEvent(step=2, phase="ACT", payload={"cost": 1.25}),
            LoopEvent(step=2, phase="EVALUATE", payload={"score": 1.0}),
            LoopEvent(
                step=2,
                phase="STOP",
                payload={"status": "SUCCEEDED", "reason": "目标已达到"},
            ),
        ],
        final_state=LoopState(
            step=2,
            value=2.0,
            goal=2.0,
            status="SUCCEEDED",
            metadata={"说明": "完成"},
        ),
    )
    expected_metrics = MetricReport.from_trace(trace)
    artifact_path = tmp_path / "nested" / "run.json"

    saved_path = save_run_artifact(artifact_path, trace)

    assert saved_path == artifact_path.resolve()
    artifact_text = artifact_path.read_text(encoding="utf-8")
    assert "目标已达到" in artifact_text
    payload = json.loads(artifact_text)
    assert {"events", "final_state", "metrics"} <= payload.keys()
    assert payload["metrics"] == {
        "steps": 2,
        "final_score": 1.0,
        "success": True,
        "cost": 2.0,
        "average_step_gain": 0.75,
    }

    loaded_trace, loaded_metrics = load_run_artifact(artifact_path)

    assert loaded_trace == trace
    assert loaded_metrics == expected_metrics
