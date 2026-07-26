"""Bridge controlled local tool executions into loop actions."""

from __future__ import annotations

from .actions import Action, ActionResult
from .models import LoopState
from .policies import Decision
from .tool_adapters import LocalToolAdapter, ToolAdapterError


class ToolAction(Action):
    """Apply registered parameterless tool decisions without changing numeric value."""

    def __init__(self, adapter: LocalToolAdapter) -> None:
        self.adapter = adapter

    def apply(self, state: LoopState, decision: Decision) -> ActionResult:
        """Execute one registered tool and expose only outcome and duration."""

        if decision.parameters != {}:
            raise ToolAdapterError("Tool decisions must not include parameters")

        execution = self.adapter.execute(decision.name)
        return ActionResult(
            state=state.with_value(state.value),
            success=execution.success,
            cost=execution.duration_seconds,
        )
