"""Bounded in-process memory for recent loop events."""

from __future__ import annotations

from collections import deque

from .models import LoopEvent


class WorkingMemory:
    """Keeps a bounded, insertion-ordered window of loop events."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self.capacity = capacity
        self._events: deque[LoopEvent] = deque(maxlen=capacity)

    def add(self, event: LoopEvent) -> None:
        """Remember one event, discarding the oldest event when full."""

        self._events.append(event)

    def recent(self, limit: int) -> list[LoopEvent]:
        """Return up to ``limit`` newest events in chronological order."""

        if limit <= 0:
            return []
        return list(self._events)[-limit:]
