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
