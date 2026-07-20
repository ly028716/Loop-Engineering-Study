from loop_engineering.models import LoopEvent, LoopState, LoopTrace


def trace_with_scores(scores: list[float]) -> LoopTrace:
    events = [
        LoopEvent(step=step, phase="EVALUATE", payload={"score": score, "success": score == 1.0})
        for step, score in enumerate(scores)
    ]
    events.extend(
        [
            LoopEvent(step=1, phase="ACT", payload={"success": True, "cost": 0.25}),
            LoopEvent(step=2, phase="ACT", payload={"success": True, "cost": 0.5}),
        ]
    )
    return LoopTrace(
        events=events,
        final_state=LoopState(
            step=max(len(scores) - 1, 0),
            value=scores[-1],
            goal=1.0,
            status="SUCCEEDED",
        ),
    )


def test_metric_report_derives_steps_score_gain_and_cost_without_mutating_trace() -> None:
    from loop_engineering.metrics import MetricReport

    trace = trace_with_scores([0.0, 0.5, 1.0])
    original_events = list(trace.events)
    original_final_state = trace.final_state

    report = MetricReport.from_trace(trace)

    assert report.steps == 2
    assert report.final_score == 1.0
    assert report.success is True
    assert report.cost == 0.75
    assert report.average_step_gain == 0.5
    assert trace.events == original_events
    assert trace.final_state is original_final_state
