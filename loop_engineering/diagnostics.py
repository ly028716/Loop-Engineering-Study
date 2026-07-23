"""Deterministic diagnostics derived exclusively from persisted loop traces."""

from __future__ import annotations

from dataclasses import dataclass

from .models import LoopEvent, LoopTrace

__all__ = ["DiagnosticFinding", "diagnose_trace"]


@dataclass(frozen=True)
class DiagnosticFinding:
    """One stable diagnostic conclusion backed by Trace event indices."""

    code: str
    severity: str
    message: str
    evidence_event_indices: tuple[int, ...]
    recommendation: str


_RULES = (
    (
        "action_failure",
        "warning",
        "One or more actions failed.",
        "Inspect feedback signals and choose a recovery action.",
    ),
    (
        "stalled_progress",
        "warning",
        "A successful action did not advance the state value.",
        "Inspect action semantics, progress signals, and no-progress stopping.",
    ),
    (
        "budget_exhausted",
        "error",
        "The run stopped at its step budget before success.",
        "Adjust the budget, action size, or early stopping strategy.",
    ),
    (
        "recovery_observed",
        "info",
        "A recovery decision followed an action failure.",
        "Compare recovery completion with its additional step cost.",
    ),
)


def _previous_observe_value(events: list[LoopEvent], action_index: int) -> float | None:
    for event in reversed(events[:action_index]):
        if event.phase == "OBSERVE" and "value" in event.payload:
            return float(event.payload["value"])
    return None


def _next_observe_value(trace: LoopTrace, action_index: int) -> float | None:
    for event in trace.events[action_index + 1 :]:
        if event.phase == "OBSERVE" and "value" in event.payload:
            return float(event.payload["value"])
    return trace.final_state.value if trace.final_state is not None else None


def _failure_indices(events: list[LoopEvent]) -> tuple[int, ...]:
    return tuple(
        index
        for index, event in enumerate(events)
        if event.phase == "ACT" and event.payload.get("success") is False
    )


def _stalled_indices(trace: LoopTrace) -> tuple[int, ...]:
    indices: list[int] = []
    for index, event in enumerate(trace.events):
        if event.phase != "ACT" or event.payload.get("success") is not True:
            continue
        before_value = _previous_observe_value(trace.events, index)
        after_value = _next_observe_value(trace, index)
        if before_value is not None and after_value is not None and before_value == after_value:
            indices.append(index)
    return tuple(indices)


def _budget_stop_index(trace: LoopTrace) -> int | None:
    if not trace.events or trace.final_state is None:
        return None
    stop_index = len(trace.events) - 1
    stop_event = trace.events[stop_index]
    if (
        stop_event.phase == "STOP"
        and str(stop_event.payload.get("reason", "")).startswith("Reached maximum steps:")
        and trace.final_state.status != "SUCCEEDED"
    ):
        return stop_index
    return None


def _recovery_evidence(
    events: list[LoopEvent], failure_indices: tuple[int, ...]
) -> tuple[int, ...]:
    if not failure_indices:
        return ()
    failure_index = failure_indices[0]
    for index, event in enumerate(events[failure_index + 1 :], start=failure_index + 1):
        parameters = event.payload.get("parameters", {})
        if (
            event.phase == "DECIDE"
            and isinstance(parameters, dict)
            and parameters.get("mode_code") == 3.0
        ):
            return failure_index, index
    return ()


def _finding(rule_index: int, evidence: tuple[int, ...]) -> DiagnosticFinding:
    code, severity, message, recommendation = _RULES[rule_index]
    return DiagnosticFinding(
        code=code,
        severity=severity,
        message=message,
        evidence_event_indices=evidence,
        recommendation=recommendation,
    )


def diagnose_trace(
    trace: LoopTrace,
    step_budget: int | None = None,
) -> list[DiagnosticFinding]:
    """Return stable rule findings from one completed or partial loop trace."""

    del step_budget
    failure_indices = _failure_indices(trace.events)
    stalled_indices = _stalled_indices(trace)
    budget_index = _budget_stop_index(trace)
    recovery_indices = _recovery_evidence(trace.events, failure_indices)
    findings: list[DiagnosticFinding] = []
    if failure_indices:
        findings.append(_finding(0, failure_indices))
    if stalled_indices:
        findings.append(_finding(1, stalled_indices))
    if budget_index is not None:
        findings.append(_finding(2, (budget_index,)))
    if recovery_indices:
        findings.append(_finding(3, recovery_indices))
    return findings
