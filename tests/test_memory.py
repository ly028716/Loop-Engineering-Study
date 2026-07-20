import pytest

from loop_engineering.models import LoopEvent


def event(step: int) -> LoopEvent:
    return LoopEvent(step=step, phase="OBSERVE", payload={"value": float(step)})


def test_working_memory_keeps_only_events_within_its_capacity() -> None:
    from loop_engineering.memory import WorkingMemory

    memory = WorkingMemory(capacity=2)
    memory.add(event(1))
    memory.add(event(2))
    memory.add(event(3))

    assert memory.recent(10) == [event(2), event(3)]


def test_working_memory_recent_returns_the_requested_tail() -> None:
    from loop_engineering.memory import WorkingMemory

    memory = WorkingMemory(capacity=3)
    for step in range(1, 4):
        memory.add(event(step))

    assert memory.recent(2) == [event(2), event(3)]
    assert memory.recent(0) == []


def test_working_memory_rejects_non_positive_capacity() -> None:
    from loop_engineering.memory import WorkingMemory

    with pytest.raises(ValueError, match="capacity"):
        WorkingMemory(capacity=0)
