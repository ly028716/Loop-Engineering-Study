import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from loop_engineering.tool_adapters import (
    LocalToolAdapter,
    ToolAdapterError,
    ToolDefinition,
)


def python_version_definition(tmp_path: Path, **overrides: object) -> ToolDefinition:
    values: dict[str, object] = {
        "name": "python-version",
        "executable": str(Path(sys.executable).resolve()),
        "arguments": ("--version",),
        "working_directory": str(tmp_path.resolve()),
        "timeout_seconds": 2.0,
    }
    values.update(overrides)
    return ToolDefinition(**values)


def test_adapter_uses_registered_fixed_argv_and_bounded_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(argv: list[str], **kwargs: object) -> SimpleNamespace:
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="x" * 6, stderr="y" * 6)

    monkeypatch.setattr("loop_engineering.tool_adapters.subprocess.run", fake_run)

    result = LocalToolAdapter(
        [python_version_definition(tmp_path)], output_limit=5
    ).execute("python-version")

    assert calls == [
        (
            [str(Path(sys.executable).resolve()), "--version"],
            {
                "cwd": str(tmp_path.resolve()),
                "shell": False,
                "capture_output": True,
                "text": True,
                "timeout": 2.0,
                "check": False,
            },
        )
    ]
    assert result.success is True
    assert result.exit_code == 0
    assert result.stdout == "x" * 5
    assert result.stderr == "y" * 5
    assert result.duration_seconds >= 0.0


def test_adapter_returns_failed_execution_for_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "loop_engineering.tool_adapters.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=7, stdout="out", stderr="err"),
    )

    result = LocalToolAdapter([python_version_definition(tmp_path)]).execute(
        "python-version"
    )

    assert result.success is False
    assert result.exit_code == 7
    assert result.stdout == "out"
    assert result.stderr == "err"


def test_adapter_returns_failed_execution_for_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            cmd=["python", "--version"],
            timeout=2.0,
            output=b"x" * 6,
            stderr=b"y" * 6,
        )

    monkeypatch.setattr("loop_engineering.tool_adapters.subprocess.run", timeout)

    result = LocalToolAdapter(
        [python_version_definition(tmp_path)], output_limit=5
    ).execute("python-version")

    assert result.success is False
    assert result.exit_code is None
    assert result.stdout == "x" * 5
    assert result.stderr == "y" * 5


def test_adapter_rejects_unknown_tool(tmp_path: Path) -> None:
    adapter = LocalToolAdapter([python_version_definition(tmp_path)])

    with pytest.raises(ToolAdapterError, match="Unregistered tool"):
        adapter.execute("unknown")


@pytest.mark.parametrize(
    ("definition", "message"),
    [
        (
            lambda tmp_path: python_version_definition(tmp_path, name=""),
            "name",
        ),
        (
            lambda tmp_path: python_version_definition(tmp_path, executable="python"),
            "executable",
        ),
        (
            lambda tmp_path: python_version_definition(
                tmp_path, working_directory="relative"
            ),
            "working directory",
        ),
        (
            lambda tmp_path: python_version_definition(
                tmp_path, working_directory=str(tmp_path / "missing")
            ),
            "working directory",
        ),
        (
            lambda tmp_path: python_version_definition(
                tmp_path, working_directory=str((tmp_path / "file").resolve())
            ),
            "working directory",
        ),
        (
            lambda tmp_path: python_version_definition(tmp_path, timeout_seconds=0.0),
            "timeout",
        ),
    ],
)
def test_adapter_rejects_invalid_definition(
    tmp_path: Path, definition, message: str
) -> None:
    (tmp_path / "file").write_text("not a directory", encoding="utf-8")

    with pytest.raises(ToolAdapterError, match=message):
        LocalToolAdapter([definition(tmp_path)])


def test_adapter_rejects_duplicate_names_and_nonpositive_output_limit(tmp_path: Path) -> None:
    definition = python_version_definition(tmp_path)

    with pytest.raises(ToolAdapterError, match="Duplicate"):
        LocalToolAdapter([definition, definition])
    with pytest.raises(ToolAdapterError, match="output limit"):
        LocalToolAdapter([definition], output_limit=0)
