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


class NoProgress(StopCondition):
    """Stops when recent evaluation scores fail to improve."""

    def __init__(self, window: int, min_score_gain: float = 0.0) -> None:
        if window < 1:
            raise ValueError("window must be at least 1")
        if min_score_gain < 0.0:
            raise ValueError("min_score_gain cannot be negative")
        self.window = window
        self.min_score_gain = min_score_gain

    def should_stop(
        self,
        state: LoopState,
        evaluation: Evaluation,
        history: Sequence[LoopEvent],
    ) -> StopDecision:
        del state, evaluation
        scores: list[float] = []
        for event in history:
            if event.phase != "EVALUATE" or "score" not in event.payload:
                continue
            try:
                scores.append(float(event.payload["score"]))
            except (TypeError, ValueError):
                continue

        if len(scores) < self.window:
            return StopDecision(stop=False, status="RUNNING", reason="")

        recent_scores = scores[-self.window :]
        gains = [
            current - previous
            for previous, current in zip(recent_scores, recent_scores[1:])
        ]
        if all(gain <= self.min_score_gain for gain in gains):
            return StopDecision(
                stop=True,
                status="STOPPED",
                reason=f"No progress for {self.window} evaluations",
            )
        return StopDecision(stop=False, status="RUNNING", reason="")
