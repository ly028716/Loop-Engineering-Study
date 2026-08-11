"""Direct-script support for nested code-repair experiments."""

from __future__ import annotations

from pathlib import Path
import sys


def prepare_script_imports(script_file: str) -> Path:
    """Add the repository root to ``sys.path`` for a direct nested script."""

    for parent in Path(script_file).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            root = parent
            break
    else:
        raise RuntimeError("Could not locate project root")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def artifact_path_for(script_file: str) -> Path:
    """Return the repository-level Artifact path for one nested experiment."""

    root = prepare_script_imports(script_file)
    return root / ".loop" / "runs" / "code-repair" / f"{Path(script_file).stem}.json"


def persist_and_print_summary(trace: object, script_file: str) -> Path:
    """Persist a nested experiment through the shared experiment helper."""

    from experiments._bootstrap import print_summary
    from loop_engineering.artifacts import save_run_artifact

    path = save_run_artifact(artifact_path_for(script_file), trace)
    print_summary(trace)
    print(f"artifact_path={path}")
    return path
