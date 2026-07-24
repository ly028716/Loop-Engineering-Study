from loop_engineering.actions import NumericAction
from loop_engineering.artifacts import save_run_artifact
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.model_adapters import HttpModelAdapter, HttpResponse
from loop_engineering.model_policy import ModelPolicy
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


class FakeTransport:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        self.payloads.append(payload)
        return HttpResponse(
            200, '{"name": "increment", "parameters": {"amount": 2}}'
        )


def test_model_policy_encodes_state_feedback_and_recent_events() -> None:
    transport = FakeTransport()
    policy = ModelPolicy(
        HttpModelAdapter("https://models.example.test", "model", "", transport)
    )
    state = LoopState(step=1, value=2.0, goal=4.0)
    feedback = Feedback(score=0.5, message="continue", signals={"error": 2.0})
    recent = [LoopEvent(step=0, phase="OBSERVE", payload={"goal": 4.0})]

    decision = policy.decide(state, feedback, recent)

    assert decision.parameters == {"amount": 2.0}
    assert transport.payloads == [
        {
            "model": "model",
            "input": {
                "state": {
                    "step": 1,
                    "value": 2.0,
                    "goal": 4.0,
                    "status": "RUNNING",
                    "metadata": {},
                },
                "feedback": {
                    "score": 0.5,
                    "message": "continue",
                    "signals": {"error": 2.0},
                },
                "recent_events": [
                    {"step": 0, "phase": "OBSERVE", "payload": {"goal": 4.0}}
                ],
            },
        }
    ]


def test_model_policy_runs_and_persists_without_api_key(tmp_path) -> None:
    transport = FakeTransport()
    policy = ModelPolicy(
        HttpModelAdapter(
            "https://models.example.test", "model", "secret-value", transport
        )
    )
    trace = LoopRunner(
        policy,
        NumericAction(),
        GoalEvaluator(0.0),
        [SuccessReached(), MaxSteps(2)],
    ).run(LoopState(step=0, value=0.0, goal=2.0))
    artifact_path = save_run_artifact(tmp_path / "run.json", trace)

    payload = artifact_path.read_text(encoding="utf-8")
    assert trace.final_state is not None and trace.final_state.status == "SUCCEEDED"
    assert "secret-value" not in payload
    assert trace.events[1].payload == {
        "name": "increment",
        "parameters": {"amount": 2.0},
    }

