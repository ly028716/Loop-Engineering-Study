"""Loop decision policies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from .models import Feedback, LoopEvent, LoopState


@dataclass(frozen=True)
class Decision:
    """An action selected by a policy and its numeric parameters."""

    name: str
    parameters: dict[str, float]


class Policy(ABC):
    """Selects a decision from the current state and previous feedback."""

    @abstractmethod
    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        """Return the next decision."""


class IncrementPolicy(Policy):
    """Moves a numeric value toward its goal by a bounded amount."""

    def __init__(self, step_size: float):
        self.step_size = step_size

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        remaining = state.goal - state.value
        amount = min(self.step_size, max(remaining, 0.0))
        return Decision(name="increment", parameters={"amount": amount})
