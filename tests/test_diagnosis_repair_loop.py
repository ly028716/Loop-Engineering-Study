import json
from pathlib import Path

from experiments.diagnosis_repair_loop import run_repair_loop
from loop_engineering.artifacts import load_run_artifact


def test_repair_loop_eliminates_targets_and_persists_evidence(tmp_path: Path) -> None:
    results = run_repair_loop(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure",
        "stalled_progress",
        "tight_budget",
    ]
    assert all(item["repair_succeeded"] is True for item in results)
    for item in results:
        targets = set(item["target_diagnostic_codes"])
        assert targets & set(item["baseline"]["diagnostic_codes"])
        assert not targets & set(item["repaired"]["diagnostic_codes"])
        assert item["repaired"]["success"] is True
        for key in ("baseline_artifact_path", "repaired_artifact_path"):
            trace, _ = load_run_artifact(item[key])
            assert trace.events[-1].phase == "STOP"
        report = json.loads(Path(item["report_path"]).read_text(encoding="utf-8"))
        assert report == {key: value for key, value in item.items() if key != "report_path"}


def test_repair_loop_keeps_case_and_diagnostic_order_stable(tmp_path: Path) -> None:
    first = run_repair_loop(tmp_path / "first")
    second = run_repair_loop(tmp_path / "second")

    assert [item["case"] for item in first] == [item["case"] for item in second]
    assert [item["baseline"]["diagnostic_codes"] for item in first] == [
        item["baseline"]["diagnostic_codes"] for item in second
    ]
