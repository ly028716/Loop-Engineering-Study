"""No-network teaching example for the external HTTP model adapter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loop_engineering.actions import NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.model_adapters import HttpModelAdapter, HttpResponse
from loop_engineering.model_policy import ModelPolicy
from loop_engineering.models import LoopState
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


class DemoTransport:
    """A transport double that demonstrates the contract without networking."""

    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        del endpoint, headers, payload, timeout_seconds
        self.calls += 1
        return HttpResponse(
            200, '{"name": "increment", "parameters": {"amount": 2.0}}'
        )


def run_external_model_adapter_demo(
    output_dir: str | Path = ".loop/runs/external-model-adapter",
) -> dict[str, object]:
    """Run a complete model-policy loop using only an injected local transport."""

    root = Path(output_dir).resolve()
    transport = DemoTransport()
    policy = ModelPolicy(
        HttpModelAdapter(
            "https://example.invalid/decide",
            "demo-model",
            "",
            transport,
        )
    )
    trace = LoopRunner(
        policy=policy,
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(2)],
    ).run(LoopState(step=0, value=0.0, goal=2.0))
    artifact_path = save_run_artifact(root / "artifact.json", trace)
    report = {
        "artifact_path": str(artifact_path),
        "status": trace.final_state.status if trace.final_state else "RUNNING",
        "decision_count": sum(event.phase == "DECIDE" for event in trace.events),
        "network_calls": transport.calls,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    """Print the no-network teaching report."""

    print(json.dumps(run_external_model_adapter_demo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

