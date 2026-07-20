"""UTF-8 JSON persistence for complete deterministic loop runs."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .metrics import MetricReport
from .models import LoopEvent, LoopState, LoopTrace


def save_run_artifact(
    path: str | Path,
    trace: LoopTrace,
    metrics: MetricReport | None = None,
) -> Path:
    """Persist a trace and its complete metrics as one replayable JSON artifact."""

    artifact_path = Path(path).resolve()
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report = metrics if metrics is not None else MetricReport.from_trace(trace)
    payload = {
        "events": [asdict(event) for event in trace.events],
        "final_state": asdict(trace.final_state) if trace.final_state is not None else None,
        "metrics": asdict(report),
    }
    with artifact_path.open("w", encoding="utf-8") as artifact_file:
        json.dump(payload, artifact_file, ensure_ascii=False, indent=2)
        artifact_file.write("\n")
    return artifact_path


def load_run_artifact(path: str | Path) -> tuple[LoopTrace, MetricReport]:
    """Restore a loop trace and its persisted metrics from a run artifact."""

    artifact_path = Path(path)
    with artifact_path.open("r", encoding="utf-8") as artifact_file:
        payload = json.load(artifact_file)

    final_state_payload = payload["final_state"]
    trace = LoopTrace(
        events=[LoopEvent(**event_payload) for event_payload in payload["events"]],
        final_state=(
            LoopState(**final_state_payload) if final_state_payload is not None else None
        ),
    )
    return trace, MetricReport(**payload["metrics"])
