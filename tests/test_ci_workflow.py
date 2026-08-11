from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_has_independent_semantic_gate_with_evidence_upload() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "semantic-gate:" in workflow
    assert "needs: test" in workflow
    assert 'python-version: "3.11"' in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python experiments/regression_gate.py" in workflow
    assert "name: semantic-gate-evidence" in workflow
    assert "path: .loop/runs/regression-gate/" in workflow
    assert "if: always()" in workflow
    assert "uses: actions/upload-artifact@v4" in workflow


def test_ci_checks_public_documentation_before_running_tests() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Run documentation integrity check" in workflow
    assert "python scripts/check_docs.py" in workflow

