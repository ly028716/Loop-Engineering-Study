from loop_engineering.actions import NumericAction
from loop_engineering.evaluators import GoalEvaluator
from loop_engineering.memory import WorkingMemory
from loop_engineering.models import Feedback, LoopEvent, LoopState
from loop_engineering.policies import Decision, IncrementPolicy, Policy
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, StopCondition, StopDecision, SuccessReached


class RecordingIncrementPolicy(IncrementPolicy):
    def __init__(self, step_size: float) -> None:
        super().__init__(step_size)
        self.received_feedback: list[Feedback] = []

    def decide(self, state: LoopState, feedback: Feedback):
        self.received_feedback.append(feedback)
        return super().decide(state, feedback)


class NeverStop(StopCondition):
    def should_stop(self, state, evaluation, history) -> StopDecision:
        return StopDecision(stop=False, status="RUNNING", reason="")


class MemoryRecordingPolicy(Policy):
    def __init__(self) -> None:
        self.recent_events: list[list[LoopEvent]] = []

    def decide(
        self,
        state: LoopState,
        feedback: Feedback,
        recent_events: list[LoopEvent],
    ) -> Decision:
        self.recent_events.append(recent_events)
        return Decision(name="increment", parameters={"amount": 1.0})


def build_numeric_runner(max_steps: int) -> LoopRunner:
    return LoopRunner(
        policy=IncrementPolicy(step_size=1.0),
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[SuccessReached(), MaxSteps(max_steps)],
    )


def test_runner_stops_when_goal_is_reached() -> None:
    trace = build_numeric_runner(max_steps=10).run(
        LoopState(step=0, value=0.0, goal=2.0)
    )

    assert trace.final_state is not None
    assert trace.final_state.status == "SUCCEEDED"
    assert trace.final_state.value == 2.0
    assert trace.events[-1].phase == "STOP"
    assert trace.events[-1].payload == {
        "status": "SUCCEEDED",
        "reason": "Evaluation reported success",
    }


def test_runner_stops_at_maximum_steps_with_ordered_events() -> None:
    trace = build_numeric_runner(max_steps=1).run(
        LoopState(step=0, value=0.0, goal=5.0)
    )

    assert trace.final_state is not None
    assert trace.final_state.status == "STOPPED"
    assert trace.final_state.step == 1
    assert trace.events[-1].payload["reason"] == "Reached maximum steps: 1"
    assert [event.phase for event in trace.events] == [
        "OBSERVE",
        "DECIDE",
        "ACT",
        "EVALUATE",
        "FEEDBACK",
        "STOP",
    ]


def test_runner_passes_previous_evaluation_as_next_feedback() -> None:
    policy = RecordingIncrementPolicy(step_size=1.0)
    runner = LoopRunner(
        policy=policy,
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[MaxSteps(2)],
    )

    runner.run(LoopState(step=0, value=0.0, goal=5.0))

    assert policy.received_feedback[0] == Feedback.empty()
    assert policy.received_feedback[1] == Feedback(
        score=0.2,
        message="Goal not reached",
        signals={"absolute_error": 4.0},
    )


def test_runner_uses_safety_limit_when_no_stop_condition_matches() -> None:
    runner = LoopRunner(
        policy=IncrementPolicy(step_size=1.0),
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[NeverStop()],
        safety_max_steps=2,
    )

    trace = runner.run(LoopState(step=0, value=0.0, goal=5.0))

    assert trace.final_state is not None
    assert trace.final_state.status == "STOPPED"
    assert trace.final_state.step == 2
    assert trace.events[-1].payload == {
        "status": "STOPPED",
        "reason": "Safety limit reached: 2",
    }


def test_runner_records_events_in_memory_and_provides_them_to_compatible_policies() -> None:
    policy = MemoryRecordingPolicy()
    memory = WorkingMemory(capacity=20)
    runner = LoopRunner(
        policy=policy,
        action=NumericAction(),
        evaluator=GoalEvaluator(tolerance=0.0),
        stop_conditions=[MaxSteps(2)],
        memory=memory,
    )

    trace = runner.run(LoopState(step=0, value=0.0, goal=5.0))

    assert [event.phase for event in policy.recent_events[0]] == ["OBSERVE"]
    assert [event.phase for event in policy.recent_events[1]] == [
        "OBSERVE",
        "DECIDE",
        "ACT",
        "EVALUATE",
        "FEEDBACK",
        "OBSERVE",
    ]
    assert memory.recent(20) == trace.events
