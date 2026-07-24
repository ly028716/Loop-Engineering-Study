from pathlib import Path

from experiments.regression_gate import run_regression_gate


def test_regression_gate_preserves_all_semantic_contracts(tmp_path: Path) -> None:
    result = run_regression_gate(tmp_path)

    assert result["passed"] is True
    assert [item["name"] for item in result["checks"]] == [
        "benchmark",
        "sensitivity",
        "diagnostics",
        "repair_loop",
    ]
    assert all(
        item["passed"] is True and item["evidence"]
        for item in result["checks"]
    )
    assert all(
        (tmp_path / name).exists()
        for name in ("benchmark", "sensitivity", "diagnostics", "repair-loop")
    )
