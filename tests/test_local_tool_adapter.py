import json
from pathlib import Path

from experiments.local_tool_adapter import run_local_tool_adapter_demo
from loop_engineering.artifacts import load_run_artifact


def test_local_tool_adapter_demo_is_replayable_and_keeps_output_out_of_artifact(
    tmp_path: Path,
) -> None:
    report = run_local_tool_adapter_demo(tmp_path)

    artifact_path = Path(report["artifact_path"])
    artifact_text = artifact_path.read_text(encoding="utf-8")
    trace, metrics = load_run_artifact(artifact_path)

    assert report["status"] == "SUCCEEDED"
    assert report["tool_name"] == "python-version"
    assert report["exit_code"] == 0
    assert report["duration_seconds"] >= 0.0
    assert "Python" in report["output"]
    assert metrics.success is True
    assert trace.events[2].payload.keys() == {"success", "cost"}
    assert report["output"] not in artifact_text
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == report
