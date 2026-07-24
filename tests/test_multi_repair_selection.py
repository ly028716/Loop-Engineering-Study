import json
from pathlib import Path

from experiments.multi_repair_selection import run_multi_repair_selection
from loop_engineering.artifacts import load_run_artifact


def test_selection_persists_candidates_and_selects_expected(tmp_path: Path) -> None:
    results = run_multi_repair_selection(tmp_path)

    assert [item["case"] for item in results] == [
        "action_failure",
        "stalled_progress",
        "tight_budget",
    ]
    assert [item["selected_candidate"] for item in results] == [
        "replace_action_step_1_5",
        "replace_action_step_2",
        "preserve_budget_step_2",
    ]
    for item in results:
        assert len(item["candidates"]) == 2
        assert item["repair_succeeded"] is True
        assert item["candidates"][0]["name"] == item["selected_candidate"]
        assert item["candidates"][0]["succeeded"] is True
        trace, _ = load_run_artifact(item["selected_artifact_path"])
        assert trace.final_state is not None
        assert trace.final_state.status == "SUCCEEDED"
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == results


def test_selection_is_stable(tmp_path: Path) -> None:
    first = run_multi_repair_selection(tmp_path / "first")
    second = run_multi_repair_selection(tmp_path / "second")

    assert [item["selected_candidate"] for item in first] == [
        item["selected_candidate"] for item in second
    ]
