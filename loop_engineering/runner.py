"""The deterministic, observable loop phase machine."""

from __future__ import annotations

from dataclasses import asdict, replace
from inspect import signature
from typing import Sequence

from .actions import Action
from .evaluators import Evaluation, Evaluator
from .memory import WorkingMemory
from .models import Feedback, LoopEvent, LoopState, LoopTrace
from .policies import Decision, Policy
from .stopping import StopCondition, StopDecision


class LoopRunner:
    """Runs policy, action, evaluation, and feedback phases until stopped."""

    def __init__(
        self,
        policy: Policy,
        action: Action,
        evaluator: Evaluator,
        stop_conditions: Sequence[StopCondition],
        safety_max_steps: int = 1_000,
        memory: WorkingMemory | None = None,
    ) -> None:
        if safety_max_steps < 1:
            raise ValueError("safety_max_steps must be at least 1")

        self.policy = policy
        self.action = action
        self.evaluator = evaluator
        self.stop_conditions = tuple(stop_conditions)
        self.safety_max_steps = safety_max_steps
        self.memory = memory if memory is not None else WorkingMemory(capacity=1_000)

    def run(self, initial_state: LoopState) -> LoopTrace:
        """Run complete observable iterations until a condition or safety stop."""

        trace = LoopTrace()
        state = initial_state
        feedback = Feedback.empty()

        for _ in range(self.safety_max_steps):
            before = state
            self._record_event(
                trace,
                "OBSERVE",
                step=state.step,
                payload={"value": state.value, "goal": state.goal},
            )
            decision = self._decide(state, feedback)
            self._record_event(
                trace, "DECIDE", step=state.step, payload=self._decision_payload(decision)
            )
            result = self.action.apply(state, decision)
            state = result.state
            self._record_event(
                trace,
                "ACT",
                step=state.step,
                payload={"success": result.success, "cost": result.cost},
            )
            evaluation = self.evaluator.evaluate(before, result)
            self._record_event(trace, "EVALUATE", step=state.step, payload=asdict(evaluation))
            feedback = Feedback(
                score=evaluation.score,
                message=evaluation.message,
                signals=dict(evaluation.signals),
            )
            self._record_event(trace, "FEEDBACK", step=state.step, payload=asdict(feedback))

            decision_to_stop = self._first_stop_decision(state, evaluation, trace.events)
            if decision_to_stop.stop:
                return self._stop(trace, state, decision_to_stop)

        return self._stop(
            trace,
            state,
            StopDecision(
                stop=True,
                status="STOPPED",
                reason=f"Safety limit reached: {self.safety_max_steps}",
            ),
        )

    def _first_stop_decision(
        self,
        state: LoopState,
        evaluation: Evaluation,
        history: Sequence[LoopEvent],
    ) -> StopDecision:
        for condition in self.stop_conditions:
            decision = condition.should_stop(state, evaluation, history)
            if decision.stop:
                return decision
        return StopDecision(stop=False, status="RUNNING", reason="")

    def _decide(self, state: LoopState, feedback: Feedback) -> Decision:
        """Call policies with recent events when their signature supports it."""

        recent_events = self.memory.recent(self.memory.capacity)
        decide = self.policy.decide
        parameters = signature(decide)
        try:
            parameters.bind(state, feedback, recent_events)
        except TypeError:
            try:
                parameters.bind(state, feedback, recent_events=recent_events)
            except TypeError:
                return decide(state, feedback)
            return decide(state, feedback, recent_events=recent_events)
        return decide(state, feedback, recent_events)

    def _record_event(
        self,
        trace: LoopTrace,
        phase: str,
        step: int,
        payload: dict[str, object],
    ) -> None:
        trace.append(phase, step=step, payload=payload)
        self.memory.add(trace.events[-1])

    @staticmethod
    def _decision_payload(decision: Decision) -> dict[str, object]:
        return {"name": decision.name, "parameters": dict(decision.parameters)}

    def _stop(
        self,
        trace: LoopTrace,
        state: LoopState,
        decision: StopDecision,
    ) -> LoopTrace:
        final_state = replace(state, status=decision.status)
        self._record_event(
            trace,
            "STOP",
            step=final_state.step,
            payload={"status": decision.status, "reason": decision.reason},
        )
        trace.final_state = final_state
        return trace
