"""Trace-derived summaries for completed loop runs."""

from __future__ import annotations

from dataclasses import dataclass

from .models import LoopTrace


@dataclass(frozen=True)
class MetricReport:
    """A non-mutating summary calculated from a loop trace."""

    steps: int
    final_score: float
    success: bool
    cost: float
    average_step_gain: float

    @classmethod
    def from_trace(cls, trace: LoopTrace) -> "MetricReport":
        """Compute metrics from recorded events without changing the trace."""

        evaluations = [event.payload for event in trace.events if event.phase == "EVALUATE"]
        scores = [float(payload["score"]) for payload in evaluations if "score" in payload]
        action_costs = [
            float(event.payload["cost"])
            for event in trace.events
            if event.phase == "ACT" and "cost" in event.payload
        ]
        steps = (
            trace.final_state.step
            if trace.final_state is not None
            else max((event.step for event in trace.events), default=0)
        )
        final_score = scores[-1] if scores else 0.0
        success = (
            trace.final_state.status == "SUCCEEDED"
            if trace.final_state is not None
            else bool(evaluations[-1].get("success", False)) if evaluations else False
        )
        average_step_gain = (
            (scores[-1] - scores[0]) / (len(scores) - 1) if len(scores) > 1 else 0.0
        )

        return cls(
            steps=steps,
            final_score=final_score,
            success=success,
            cost=sum(action_costs),
            average_step_gain=average_step_gain,
        )
