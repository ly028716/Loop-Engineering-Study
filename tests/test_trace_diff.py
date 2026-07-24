from loop_engineering.metrics import MetricReport
from loop_engineering.models import LoopState, LoopTrace
from loop_engineering.trace_diff import compare_traces


def _metrics(*, score: float = 1.0) -> MetricReport:
    return MetricReport(
        steps=1,
        final_score=score,
        success=True,
        cost=1.0,
        average_step_gain=0.0,
    )


def test_compare_traces_returns_identical_for_matching_boundaries() -> None:
    trace = LoopTrace(
        final_state=LoopState(step=1, value=1.0, goal=1.0, status="SUCCEEDED")
    )

    result = compare_traces(trace, trace, _metrics(), _metrics())

    assert result.identical is True
    assert result.first_difference is None
    assert result.baseline_event_count == result.repaired_event_count == 0


def test_compare_traces_reports_first_payload_field_difference() -> None:
    baseline = LoopTrace()
    baseline.append("DECIDE", 0, {"name": "increment", "parameters": {"size": 1.0}})
    repaired = LoopTrace()
    repaired.append("DECIDE", 0, {"name": "increment", "parameters": {"size": 2.0}})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.identical is False
    assert result.first_difference is not None
    assert result.first_difference.scope == "event"
    assert result.first_difference.event_index == 0
    assert result.first_difference.field_path == ("payload", "parameters", "size")
    assert result.first_difference.baseline_value == 1.0
    assert result.first_difference.repaired_value == 2.0


def test_compare_traces_stops_at_step_difference_before_payload() -> None:
    baseline = LoopTrace()
    baseline.append("OBSERVE", 0, {"value": 0.0})
    repaired = LoopTrace()
    repaired.append("OBSERVE", 1, {"value": 9.0})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.field_path == ("step",)
    assert result.first_difference.baseline_value == 0
    assert result.first_difference.repaired_value == 1


def test_compare_traces_reports_phase_difference_before_payload() -> None:
    baseline = LoopTrace()
    baseline.append("OBSERVE", 0, {"value": 0.0})
    repaired = LoopTrace()
    repaired.append("DECIDE", 0, {"value": 9.0})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.field_path == ("phase",)
    assert result.first_difference.baseline_value == "OBSERVE"
    assert result.first_difference.repaired_value == "DECIDE"


def test_compare_traces_reports_added_event_after_matching_prefix() -> None:
    baseline = LoopTrace()
    repaired = LoopTrace()
    repaired.append("STOP", 0, {"status": "FAILED"})

    result = compare_traces(baseline, repaired, _metrics(), _metrics())

    assert result.first_difference is not None
    assert result.first_difference.scope == "event_count"
    assert result.first_difference.event_index == 0
    assert result.first_difference.baseline_value is None
    assert result.first_difference.repaired_value == {
        "step": 0,
        "phase": "STOP",
        "payload": {"status": "FAILED"},
    }


def test_compare_traces_reports_final_state_then_metric_difference() -> None:
    baseline = LoopTrace(
        final_state=LoopState(step=1, value=1.0, goal=1.0, status="SUCCEEDED")
    )
    repaired = LoopTrace(
        final_state=LoopState(step=1, value=0.0, goal=1.0, status="FAILED")
    )

    state_result = compare_traces(baseline, repaired, _metrics(), _metrics())
    metric_result = compare_traces(baseline, baseline, _metrics(), _metrics(score=0.5))

    assert state_result.first_difference is not None
    assert state_result.first_difference.scope == "final_state"
    assert metric_result.first_difference is not None
    assert metric_result.first_difference.scope == "metrics"
    assert metric_result.baseline_metrics["final_score"] == 1.0
    assert metric_result.repaired_metrics["final_score"] == 0.5
