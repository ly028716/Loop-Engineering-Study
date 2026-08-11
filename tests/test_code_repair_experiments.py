"""Behavior contracts for the deterministic code-repair course experiments."""

from pathlib import Path
import sys

from experiments.code_repair import baseline, feedback_strategy, stopping_policy
from experiments.code_repair._bootstrap import artifact_path_for, prepare_script_imports


def test_nested_bootstrap_adds_project_root_before_domain_imports() -> None:
    script_file = Path(__file__).parents[1] / "experiments" / "code_repair" / "baseline.py"

    root = prepare_script_imports(str(script_file))

    assert root / "pyproject.toml" == Path(__file__).parents[1] / "pyproject.toml"
    assert str(root) in sys.path


def test_nested_experiment_artifacts_live_under_the_repository_run_directory() -> None:
    script_file = Path(__file__).parents[1] / "experiments" / "code_repair" / "baseline.py"

    assert artifact_path_for(str(script_file)) == (
        Path(__file__).parents[1] / ".loop" / "runs" / "code-repair" / "baseline.json"
    )


def test_baseline_repeats_an_ineffective_candidate_and_stops_at_budget() -> None:
    trace = baseline.run()

    decisions = [event.payload for event in trace.events if event.phase == "DECIDE"]

    assert [item["parameters"]["candidate"] for item in decisions] == [
        "off_by_one",
        "off_by_one",
        "off_by_one",
    ]
    assert trace.final_state.status == "STOPPED"
    assert trace.events[-1].payload["reason"] == "Reached maximum steps: 3"


def test_feedback_strategy_succeeds_on_the_second_candidate() -> None:
    trace = feedback_strategy.run()

    decisions = [event.payload for event in trace.events if event.phase == "DECIDE"]

    assert [item["parameters"]["candidate"] for item in decisions] == [
        "off_by_one",
        "fix_boundary",
    ]
    assert trace.final_state.status == "SUCCEEDED"


def test_no_progress_stops_before_budget() -> None:
    trace = stopping_policy.run()

    assert trace.final_state.step < 5
    assert trace.events[-1].payload["reason"] == "No progress for 2 evaluations"
