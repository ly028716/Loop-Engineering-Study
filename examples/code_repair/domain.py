"""Deterministic code-repair domain adapted to the generic loop interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from loop_engineering.actions import Action, ActionResult
from loop_engineering.evaluators import Evaluation, Evaluator
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.policies import Decision, Policy


@dataclass(frozen=True)
class RepairCandidate:
    """A named candidate implementation for a fixed deterministic case."""

    name: str
    transform: Callable[[int], int]


@dataclass(frozen=True)
class RepairCase:
    """Candidate implementations and expected results for a repair scenario."""

    name: str
    candidates: dict[str, RepairCandidate]
    test_cases: tuple[tuple[int, int], ...]
    expected_candidate: str


class CandidateRepairAction(Action):
    """Apply one candidate in memory without editing source files."""

    def __init__(self, case: RepairCase):
        self.case = case

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        candidate_name = str(decision.parameters["candidate"])
        candidate = self.case.candidates[candidate_name]
        failed_inputs = tuple(
            value
            for value, expected in self.case.test_cases
            if candidate.transform(value) != expected
        )
        return ActionResult(
            state=state.with_value(
                1.0 if not failed_inputs else 0.0,
                candidate_name=candidate.name,
                tests_passed=not failed_inputs,
                failed_inputs=failed_inputs,
            ),
            success=True,
            cost=1.0,
        )


class TestCaseEvaluator(Evaluator):
    """Judge candidates by their deterministic behavioral test cases."""

    __test__ = False

    def __init__(self, case: RepairCase):
        self.case = case

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        del before
        failed_inputs = tuple(result.state.metadata["failed_inputs"])
        tests_passed = bool(result.state.metadata["tests_passed"])
        return Evaluation(
            score=1.0 if tests_passed else 0.0,
            success=tests_passed,
            message="All tests passed" if tests_passed else "Tests still failing",
            signals={
                "tests_passed": tests_passed,
                "failed_test_count": len(failed_inputs),
                "failed_input": failed_inputs[0] if failed_inputs else None,
                "recommended_candidate": (
                    "" if tests_passed else self.case.expected_candidate
                ),
            },
        )


class RepeatedCandidatePolicy(Policy):
    """Always retries the same named candidate."""

    def __init__(self, candidate_name: str):
        self.candidate_name = candidate_name

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del state, feedback, recent_events
        return Decision("apply_candidate", {"candidate": self.candidate_name})


class FeedbackAwareRepairPolicy(Policy):
    """Select a suggested candidate after evaluator feedback."""

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        del state, recent_events
        candidate_name = str(feedback.signals.get("recommended_candidate", "off_by_one"))
        return Decision("apply_candidate", {"candidate": candidate_name})


def boundary_repair_case() -> RepairCase:
    """Return a two-test boundary repair case with one wrong and one right fix."""

    return RepairCase(
        name="boundary_repair",
        candidates={
            "off_by_one": RepairCandidate("off_by_one", lambda value: value + 1),
            "fix_boundary": RepairCandidate(
                "fix_boundary", lambda value: min(value + 1, 1)
            ),
        },
        test_cases=((0, 1), (1, 1)),
        expected_candidate="fix_boundary",
    )


def initial_repair_state() -> LoopState:
    """Return the initial state for the course's code-repair loop."""

    return LoopState(step=0, value=0.0, goal=1.0)
