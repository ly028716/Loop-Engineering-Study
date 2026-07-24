"""Read-only, deterministic first-difference comparison for loop traces."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .metrics import MetricReport
from .models import LoopTrace

_MISSING = object()


@dataclass(frozen=True)
class TraceDifference:
    """The first observable difference between a baseline and repaired run."""

    scope: str
    event_index: int | None
    step: int | None
    phase: str | None
    field_path: tuple[str | int, ...]
    baseline_value: object
    repaired_value: object


@dataclass(frozen=True)
class TraceComparison:
    """A JSON-serializable comparison result and run-boundary snapshots."""

    identical: bool
    first_difference: TraceDifference | None
    baseline_event_count: int
    repaired_event_count: int
    baseline_final_state: dict[str, object] | None
    repaired_final_state: dict[str, object] | None
    baseline_metrics: dict[str, object]
    repaired_metrics: dict[str, object]


def _first_value_difference(
    baseline: object,
    repaired: object,
    path: tuple[str | int, ...] = (),
) -> tuple[tuple[str | int, ...], object, object] | None:
    if baseline == repaired:
        return None
    if isinstance(baseline, dict) and isinstance(repaired, dict):
        for key in sorted(set(baseline) | set(repaired)):
            difference = _first_value_difference(
                baseline.get(key, _MISSING), repaired.get(key, _MISSING), path + (key,)
            )
            if difference is not None:
                return difference
    if isinstance(baseline, list) and isinstance(repaired, list):
        if len(baseline) != len(repaired):
            return path + ("length",), len(baseline), len(repaired)
        for index, (baseline_value, repaired_value) in enumerate(zip(baseline, repaired)):
            difference = _first_value_difference(
                baseline_value, repaired_value, path + (index,)
            )
            if difference is not None:
                return difference
    return path, baseline, repaired


def _snapshot(value: object) -> dict[str, object] | None:
    return asdict(value) if value is not None else None


def _comparison(
    baseline: LoopTrace,
    repaired: LoopTrace,
    baseline_metrics: MetricReport,
    repaired_metrics: MetricReport,
    first_difference: TraceDifference | None,
) -> TraceComparison:
    return TraceComparison(
        identical=first_difference is None,
        first_difference=first_difference,
        baseline_event_count=len(baseline.events),
        repaired_event_count=len(repaired.events),
        baseline_final_state=_snapshot(baseline.final_state),
        repaired_final_state=_snapshot(repaired.final_state),
        baseline_metrics=asdict(baseline_metrics),
        repaired_metrics=asdict(repaired_metrics),
    )


def compare_traces(
    baseline: LoopTrace,
    repaired: LoopTrace,
    baseline_metrics: MetricReport,
    repaired_metrics: MetricReport,
) -> TraceComparison:
    """Return the first index-aligned event difference and both run summaries."""

    for index, (baseline_event, repaired_event) in enumerate(
        zip(baseline.events, repaired.events)
    ):
        for field, baseline_value, repaired_value in (
            ("step", baseline_event.step, repaired_event.step),
            ("phase", baseline_event.phase, repaired_event.phase),
        ):
            if baseline_value != repaired_value:
                return _comparison(
                    baseline,
                    repaired,
                    baseline_metrics,
                    repaired_metrics,
                    TraceDifference(
                        scope="event",
                        event_index=index,
                        step=baseline_event.step,
                        phase=baseline_event.phase,
                        field_path=(field,),
                        baseline_value=baseline_value,
                        repaired_value=repaired_value,
                    ),
                )
        payload_difference = _first_value_difference(
            baseline_event.payload, repaired_event.payload, ("payload",)
        )
        if payload_difference is not None:
            path, baseline_value, repaired_value = payload_difference
            return _comparison(
                baseline,
                repaired,
                baseline_metrics,
                repaired_metrics,
                TraceDifference(
                    scope="event",
                    event_index=index,
                    step=baseline_event.step,
                    phase=baseline_event.phase,
                    field_path=path,
                    baseline_value=baseline_value,
                    repaired_value=repaired_value,
                ),
            )
    if len(baseline.events) != len(repaired.events):
        index = min(len(baseline.events), len(repaired.events))
        baseline_event = baseline.events[index] if index < len(baseline.events) else None
        repaired_event = repaired.events[index] if index < len(repaired.events) else None
        event = baseline_event if baseline_event is not None else repaired_event
        return _comparison(
            baseline,
            repaired,
            baseline_metrics,
            repaired_metrics,
            TraceDifference(
                scope="event_count",
                event_index=index,
                step=event.step if event is not None else None,
                phase=event.phase if event is not None else None,
                field_path=("events", index),
                baseline_value=asdict(baseline_event) if baseline_event is not None else None,
                repaired_value=asdict(repaired_event) if repaired_event is not None else None,
            ),
        )
    final_state_difference = _first_value_difference(
        _snapshot(baseline.final_state), _snapshot(repaired.final_state)
    )
    if final_state_difference is not None:
        path, baseline_value, repaired_value = final_state_difference
        return _comparison(
            baseline,
            repaired,
            baseline_metrics,
            repaired_metrics,
            TraceDifference(
                scope="final_state",
                event_index=None,
                step=None,
                phase=None,
                field_path=path,
                baseline_value=baseline_value,
                repaired_value=repaired_value,
            ),
        )
    metric_difference = _first_value_difference(
        asdict(baseline_metrics), asdict(repaired_metrics)
    )
    if metric_difference is not None:
        path, baseline_value, repaired_value = metric_difference
        return _comparison(
            baseline,
            repaired,
            baseline_metrics,
            repaired_metrics,
            TraceDifference(
                scope="metrics",
                event_index=None,
                step=None,
                phase=None,
                field_path=path,
                baseline_value=baseline_value,
                repaired_value=repaired_value,
            ),
        )
    return _comparison(baseline, repaired, baseline_metrics, repaired_metrics, None)


__all__ = ["TraceComparison", "TraceDifference", "compare_traces"]
