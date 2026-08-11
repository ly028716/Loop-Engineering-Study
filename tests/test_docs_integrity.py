"""Tests for the portable public-documentation integrity check."""

from __future__ import annotations

from pathlib import Path

from scripts.check_docs import check_repository


def test_check_repository_accepts_valid_utf8_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Study\n\n[Guide](docs/guide.md)\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")

    assert check_repository(tmp_path) == []


def test_check_repository_reports_missing_relative_markdown_target(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("[Missing](docs/missing.md)\n", encoding="utf-8")

    assert check_repository(tmp_path) == [
        "README.md: missing local target docs/missing.md"
    ]


def test_check_repository_reports_invalid_utf8_markdown(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_bytes(b"\xff\xfe")

    assert check_repository(tmp_path) == ["README.md: not valid UTF-8"]


def test_check_repository_ignores_links_in_fenced_code_blocks(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "```markdown\n[Example](docs/not-a-link.md)\n```\n",
        encoding="utf-8",
    )

    assert check_repository(tmp_path) == []


def test_check_repository_ignores_development_archive(tmp_path: Path) -> None:
    archive = tmp_path / "docs" / "superpowers"
    archive.mkdir(parents=True)
    (archive / "historical-plan.md").write_text(
        "[Historical link](docs/no-longer-current.md)\n",
        encoding="utf-8",
    )

    assert check_repository(tmp_path) == []


def test_check_repository_ignores_linked_worktrees(tmp_path: Path) -> None:
    linked_worktree = tmp_path / ".worktrees" / "other-checkout"
    linked_worktree.mkdir(parents=True)
    (linked_worktree / "README.md").write_text(
        "[Historical link](docs/no-longer-current.md)\n",
        encoding="utf-8",
    )

    assert check_repository(tmp_path) == []
