"""Contracts for the public learning entry points."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_chinese_readme_is_course_first() -> None:
    readme = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    for expected in (
        "已会 Python",
        "45 分钟",
        "为什么循环没有改进",
        "course/01-baseline.md",
        "experiments/code_repair/baseline.py",
    ):
        assert expected in readme


def test_reference_and_advanced_indexes_separate_follow_up_material() -> None:
    reference = (PROJECT_ROOT / "docs" / "reference" / "index.md").read_text(
        encoding="utf-8"
    )
    advanced = (PROJECT_ROOT / "docs" / "advanced" / "index.md").read_text(
        encoding="utf-8"
    )

    assert "architecture.md" in reference
    assert "external-model-adapter.md" in advanced
