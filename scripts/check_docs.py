"""Validate the repository's public Markdown documentation without dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")


def without_fenced_code(content: str) -> str:
    """Remove fenced code blocks before scanning Markdown links."""

    lines: list[str] = []
    in_fence = False
    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def check_repository(root: Path) -> list[str]:
    """Return UTF-8 and local-link errors for Markdown files below ``root``."""

    errors: list[str] = []
    for markdown_file in sorted(root.rglob("*.md")):
        relative_file = markdown_file.relative_to(root)
        if relative_file.parts[:2] == ("docs", "superpowers"):
            continue
        try:
            content = markdown_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{relative_file}: not valid UTF-8")
            continue

        for target in MARKDOWN_LINK_PATTERN.findall(without_fenced_code(content)):
            if target.startswith(EXTERNAL_PREFIXES) or target.startswith("#"):
                continue
            local_target = target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
            if local_target and not (markdown_file.parent / local_target).exists():
                errors.append(f"{relative_file}: missing local target {local_target}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = check_repository(root)
    if errors:
        print("Documentation integrity check failed:")
        print("\n".join(errors))
        return 1
    print("Documentation integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
