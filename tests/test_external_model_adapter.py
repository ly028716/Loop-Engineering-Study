import json
from pathlib import Path

from experiments.external_model_adapter import run_external_model_adapter_demo
from loop_engineering.artifacts import load_run_artifact


def test_external_model_adapter_demo_is_replayable_and_does_not_need_network(
    tmp_path: Path,
) -> None:
    result = run_external_model_adapter_demo(tmp_path)

    assert result["status"] == "SUCCEEDED"
    assert result["decision_count"] == 1
    assert result["network_calls"] == 1
    artifact_path = Path(result["artifact_path"])
    trace, metrics = load_run_artifact(artifact_path)
    assert metrics.success is True
    assert trace.events[1].payload == {
        "name": "increment",
        "parameters": {"amount": 2.0},
    }
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == result

