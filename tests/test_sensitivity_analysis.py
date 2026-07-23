from pathlib import Path

from experiments.sensitivity_analysis import run_sensitivity
from loop_engineering.artifacts import load_run_artifact


BASELINE = {"goal_distance": 6, "failure_attempt": 2, "step_budget": 8}
PARAMETER_FAMILIES = set(BASELINE)


def test_sensitivity_runs_nine_isolated_configurations(tmp_path: Path) -> None:
    result = run_sensitivity(tmp_path)

    assert len(result["configurations"]) == 9
    assert len(result["runs"]) == 36
    assert all(Path(item["artifact_path"]).exists() for item in result["runs"])

    for item in result["runs"]:
        trace, _ = load_run_artifact(item["artifact_path"])
        assert trace.events[-1].phase == "STOP"

    for configuration in result["configurations"]:
        family = configuration["parameter_family"]
        values = configuration["parameters"]
        assert configuration["baseline"] == BASELINE
        assert len(configuration["runs"]) == 4
        assert len(configuration["artifact_paths"]) == 4
        assert values[family] == configuration["parameter_value"]
        for other in PARAMETER_FAMILIES - {family}:
            assert values[other] == BASELINE[other]


def test_sensitivity_ranking_and_flip_analysis_are_stable(tmp_path: Path) -> None:
    result = run_sensitivity(tmp_path)

    for configuration in result["configurations"]:
        ranking = configuration["ranking"]
        assert [item["rank"] for item in ranking] == [1, 2, 3, 4]
        assert ranking == sorted(
            ranking,
            key=lambda item: (-item["total_score"], item["steps"], item["strategy"]),
        )

    analysis = result["flip_analysis"]
    assert set(analysis) == PARAMETER_FAMILIES
    assert all(entry["no_flip"] == (not entry["flips"]) for entry in analysis.values())
    assert all(
        flip["from_value"] < flip["to_value"]
        for entry in analysis.values()
        for flip in entry["flips"]
    )
