"""Evaluation of action results against loop goals."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .actions import ActionResult
from .models import LoopState


@dataclass(frozen=True)
class Evaluation:
    """The quality and goal status of an action result."""

    score: float
    success: bool
    message: str
    signals: dict[str, float]


class Evaluator(ABC):
    """Scores an action result relative to the state it started from."""

    @abstractmethod
    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        """Return an evaluation of the action result."""


class GoalEvaluator(Evaluator):
    """Scores proximity to the result state's numeric goal."""

    def __init__(self, tolerance: float):
        self.tolerance = tolerance

    def evaluate(self, before: LoopState, result: ActionResult) -> Evaluation:
        error = abs(result.state.goal - result.state.value)
        success = error <= self.tolerance
        return Evaluation(
            score=1.0 / (1.0 + error),
            success=success,
            message="Goal reached" if success else "Goal not reached",
            signals={"absolute_error": error},
        )
