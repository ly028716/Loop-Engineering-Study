"""Loop actions that apply decisions to states."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .models import LoopState
from .policies import Decision


@dataclass(frozen=True)
class ActionResult:
    """The state yielded by an action together with its outcome metadata."""

    state: LoopState
    success: bool
    cost: float


class Action(ABC):
    """Applies a decision to a loop state."""

    @abstractmethod
    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        """Apply a decision and return its result."""


class NumericAction(Action):
    """Applies supported numeric decisions without mutating the input state."""

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        if decision.name != "increment":
            raise ValueError(f"Unsupported decision: {decision.name}")

        amount = decision.parameters["amount"]
        return ActionResult(
            state=state.with_value(state.value + amount),
            success=True,
            cost=amount,
        )
