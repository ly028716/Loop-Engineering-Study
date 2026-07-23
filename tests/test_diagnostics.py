from pathlib import Path

from experiments.adaptive_strategy import build_experiment as build_adaptive_experiment
from experiments.benchmark_suite import build_scenario
from experiments.failure_modes import build_experiment as build_failure_experiment
from loop_engineering.diagnostics import diagnose_trace


def _trace_from(builder_result: tuple[object, ...]):
    runner, initial_state, *_ = builder_result
    return runner.run(initial_state)


def test_diagnose_trace_reports_failure_and_recovery_evidence(tmp_path: Path) -> None:
    failure_trace = _trace_from(build_failure_experiment("action_failure", tmp_path))
    recovery_trace = _trace_from(build_adaptive_experiment("adaptive", tmp_path))

    failure = diagnose_trace(failure_trace)
    recovery = diagnose_trace(recovery_trace)

    assert [item.code for item in failure] == ["action_failure"]
    assert [item.code for item in recovery] == [
        "action_failure",
        "recovery_observed",
    ]
    assert failure[0].recommendation == (
        "Inspect feedback signals and choose a recovery action."
    )
    assert recovery[1].severity == "info"
    assert all(
        0 <= index < len(failure_trace.events)
        for item in failure
        for index in item.evidence_event_indices
    )
    assert all(
        0 <= index < len(recovery_trace.events)
        for item in recovery
        for index in item.evidence_event_indices
    )


def test_diagnose_trace_reports_stall_and_budget_exhaustion() -> None:
    stalled_runner, stalled_state, stalled_budget = build_scenario(
        "stalled_progress", "fixed"
    )
    tight_runner, tight_state, tight_budget = build_scenario("tight_budget", "fixed")

    stalled_trace = stalled_runner.run(stalled_state)
    tight_trace = tight_runner.run(tight_state)
    stalled = diagnose_trace(stalled_trace, stalled_budget)
    tight = diagnose_trace(tight_trace, tight_budget)

    assert [item.code for item in stalled] == [
        "stalled_progress",
        "budget_exhausted",
    ]
    assert [item.code for item in tight] == ["budget_exhausted"]
    assert stalled[1].severity == "error"
    assert all(
        0 <= index < len(stalled_trace.events)
        for item in stalled
        for index in item.evidence_event_indices
    )
    assert all(
        0 <= index < len(tight_trace.events)
        for item in tight
        for index in item.evidence_event_indices
    )
    assert stalled == diagnose_trace(stalled_runner.run(stalled_state), stalled_budget)
