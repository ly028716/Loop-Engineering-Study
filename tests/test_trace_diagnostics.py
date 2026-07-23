import json
from pathlib import Path

from experiments.trace_diagnostics import run_diagnostics
from loop_engineering.artifacts import load_run_artifact


def test_trace_diagnostics_persists_four_cases_and_reports(tmp_path: Path) -> None:
    results = run_diagnostics(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure",
        "stalled_progress",
        "tight_budget",
        "adaptive_recovery",
    ]
    assert {finding["code"] for item in results for finding in item["findings"]} == {
        "action_failure",
        "stalled_progress",
        "budget_exhausted",
        "recovery_observed",
    }
    for item in results:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"
        report = json.loads(Path(item["report_path"]).read_text(encoding="utf-8"))
        assert report["case"] == item["case"]
        assert report["step_budget"] == item["step_budget"]
        assert report["findings"] == item["findings"]
