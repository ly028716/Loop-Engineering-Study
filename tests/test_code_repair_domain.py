"""Deterministic code-repair domain contracts for the core course."""

from examples.code_repair.domain import (
    CandidateRepairAction,
    FeedbackAwareRepairPolicy,
    TestCaseEvaluator,
    boundary_repair_case,
    initial_repair_state,
)
from loop_engineering.models import Feedback
from loop_engineering.policies import Decision


def test_evaluator_rejects_a_plausible_but_wrong_candidate() -> None:
    case = boundary_repair_case()
    state = initial_repair_state()
    result = CandidateRepairAction(case).apply(
        state,
        Decision("apply_candidate", {"candidate": "off_by_one"}),
    )

    evaluation = TestCaseEvaluator(case).evaluate(state, result)

    assert result.success is True
    assert evaluation.success is False
    assert evaluation.signals["failed_test_count"] == 1
    assert evaluation.signals["recommended_candidate"] == "fix_boundary"


def test_feedback_aware_policy_uses_recommended_candidate() -> None:
    decision = FeedbackAwareRepairPolicy().decide(
        initial_repair_state(),
        Feedback(
            score=0.0,
            message="boundary test failed",
            signals={"recommended_candidate": "fix_boundary"},
        ),
    )

    assert decision.name == "apply_candidate"
    assert decision.parameters == {"candidate": "fix_boundary"}
