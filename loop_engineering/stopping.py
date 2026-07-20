"""Explicit stopping conditions for observable loop runs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from .evaluators import Evaluation
from .models import LoopEvent, LoopState


@dataclass(frozen=True)
class StopDecision:
    """Describes whether a loop should stop and the resulting state."""

    stop: bool
    status: str
    reason: str


class StopCondition(ABC):
    """Determines whether an evaluated loop iteration should end."""

    @abstractmethod
    def should_stop(
        self,
        state: LoopState,
        evaluation: Evaluation,
        history: Sequence[LoopEvent],
    ) -> StopDecision:
        """Return the decision produced from the completed iteration."""


class SuccessReached(StopCondition):
    """Stops successfully once evaluation reports that the goal was met."""

    def should_stop(
        self,
        state: LoopState,
        evaluation: Evaluation,
        history: Sequence[LoopEvent],
    ) -> StopDecision:
        if evaluation.success:
            return StopDecision(
                stop=True,
                status="SUCCEEDED",
                reason="Evaluation reported success",
            )
        return StopDecision(stop=False, status="RUNNING", reason="")


class MaxSteps(StopCondition):
    """Stops when the completed state's step count reaches a fixed limit."""

    def __init__(self, max_steps: int) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.max_steps = max_steps

    def should_stop(
        self,
        state: LoopState,
        evaluation: Evaluation,
        history: Sequence[LoopEvent],
    ) -> StopDecision:
        if state.step >= self.max_steps:
            return StopDecision(
                stop=True,
                status="STOPPED",
                reason=f"Reached maximum steps: {self.max_steps}",
            )
        return StopDecision(stop=False, status="RUNNING", reason="")
