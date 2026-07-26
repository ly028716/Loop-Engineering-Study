"""Controlled local subprocess adapters for diagnostic loop actions."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class ToolAdapterError(ValueError):
    """Raised when a local tool violates the registration or selection contract."""


@dataclass(frozen=True)
class ToolDefinition:
    """One explicitly registered local diagnostic command."""

    name: str
    executable: str
    arguments: tuple[str, ...]
    working_directory: str
    timeout_seconds: float


@dataclass(frozen=True)
class ToolExecution:
    """The bounded observable result of one registered tool invocation."""

    success: bool
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float


class LocalToolAdapter:
    """Execute only fixed, construction-time registered local commands."""

    def __init__(
        self, definitions: Sequence[ToolDefinition], output_limit: int = 1_000
    ) -> None:
        if output_limit <= 0:
            raise ToolAdapterError("Tool output limit must be positive")

        self._definitions: dict[str, ToolDefinition] = {}
        for definition in definitions:
            self._validate_definition(definition)
            if definition.name in self._definitions:
                raise ToolAdapterError(f"Duplicate tool name: {definition.name}")
            self._definitions[definition.name] = definition
        self.output_limit = output_limit

    def execute(self, name: str) -> ToolExecution:
        """Run a registered command without accepting any dynamic arguments."""

        definition = self._definitions.get(name)
        if definition is None:
            raise ToolAdapterError(f"Unregistered tool: {name}")

        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [definition.executable, *definition.arguments],
                cwd=definition.working_directory,
                shell=False,
                capture_output=True,
                text=True,
                timeout=definition.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            return ToolExecution(
                success=False,
                exit_code=None,
                stdout=self._bound(error.stdout),
                stderr=self._bound(error.stderr),
                duration_seconds=time.perf_counter() - started,
            )

        return ToolExecution(
            success=completed.returncode == 0,
            exit_code=completed.returncode,
            stdout=self._bound(completed.stdout),
            stderr=self._bound(completed.stderr),
            duration_seconds=time.perf_counter() - started,
        )

    @staticmethod
    def _validate_definition(definition: ToolDefinition) -> None:
        if not definition.name.strip():
            raise ToolAdapterError("Tool name must not be empty")
        if not Path(definition.executable).is_absolute():
            raise ToolAdapterError("Tool executable must be an absolute path")

        working_directory = Path(definition.working_directory)
        if not working_directory.is_absolute() or not working_directory.is_dir():
            raise ToolAdapterError(
                "Tool working directory must be an existing absolute directory"
            )
        if definition.timeout_seconds <= 0:
            raise ToolAdapterError("Tool timeout must be positive")

    def _bound(self, output: str | bytes | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return output[: self.output_limit]
