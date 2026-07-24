"""Policy adapter that obtains Decisions from an explicit external model."""

from __future__ import annotations

from dataclasses import asdict
from typing import Sequence

from .model_adapters import HttpModelAdapter
from .models import Feedback, LoopEvent, LoopState
from .policies import Decision, Policy


class ModelPolicy(Policy):
    """Encode observable loop context and delegate decision selection to a model."""

    def __init__(self, adapter: HttpModelAdapter) -> None:
        self.adapter = adapter

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: Sequence[LoopEvent] | None = None,
    ) -> Decision:
        return self.adapter.complete(
            {
                "state": asdict(state),
                "feedback": asdict(feedback),
                "recent_events": [asdict(event) for event in recent_events or ()],
            }
        )

