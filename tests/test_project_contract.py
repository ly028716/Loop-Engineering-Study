"""Project-level documentation contracts for the completed learning baseline."""

from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEARNING_PATH = PROJECT_ROOT / "docs" / "learning-path.md"
CONCEPTS = PROJECT_ROOT / "docs" / "concepts.md"


@pytest.mark.parametrize(
    "relative_path",
    [
        "theory/loop-models.md",
        "theory/feedback-systems.md",
        "experiments/basic_loop.py",
    ],
)
def test_learning_path_links_to_existing_files(relative_path: str) -> None:
    text = LEARNING_PATH.read_text(encoding="utf-8")
    link_target = f"../{relative_path}"

    assert relative_path in text
    assert f"]({link_target})" in text
    assert (PROJECT_ROOT / relative_path).is_file()
    assert (LEARNING_PATH.parent / link_target).resolve().is_file()


def test_concepts_describe_and_link_the_implemented_runtime() -> None:
    text = CONCEPTS.read_text(encoding="utf-8")

    assert "不定义运行时模型" not in text
    for relative_path in (
        "loop_engineering/models.py",
        "loop_engineering/runner.py",
        "loop_engineering/policies.py",
        "loop_engineering/actions.py",
        "loop_engineering/evaluators.py",
        "loop_engineering/stopping.py",
        "loop_engineering/memory.py",
        "loop_engineering/metrics.py",
        "loop_engineering/artifacts.py",
        "loop_engineering/cli.py",
        "experiments/basic_loop.py",
    ):
        link_target = f"../{relative_path}"
        assert f"]({link_target})" in text
        assert (CONCEPTS.parent / link_target).resolve().is_file()
