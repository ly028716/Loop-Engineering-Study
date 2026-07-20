"""Clean-build smoke tests for the installable project surface."""

from __future__ import annotations

from pathlib import Path
import tomllib

from setuptools import find_packages


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_package_discovery_includes_runtime_and_experiments() -> None:
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    include = pyproject["tool"]["setuptools"]["packages"]["find"]["include"]

    assert include == ["loop_engineering*", "experiments*"]
    discovered = set(
        find_packages(
            where=str(PROJECT_ROOT),
            include=include,
        )
    )
    assert {"loop_engineering", "experiments"} <= discovered
