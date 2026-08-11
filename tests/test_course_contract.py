"""Contracts for the learner-facing Loop Engineering course."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_course_starts_from_the_failed_code_repair_baseline() -> None:
    lesson = (PROJECT_ROOT / "course" / "01-baseline.md").read_text(encoding="utf-8")

    assert "experiments/code_repair/baseline.py" in lesson
    assert "Action succeeded" in lesson
    assert "evaluation failed" in lesson


def test_improvement_lesson_requires_before_after_artifact_evidence() -> None:
    lesson = (PROJECT_ROOT / "course" / "03-improve-the-loop.md").read_text(encoding="utf-8")

    assert "before" in lesson.lower()
    assert "after" in lesson.lower()
    assert "Artifact" in lesson
