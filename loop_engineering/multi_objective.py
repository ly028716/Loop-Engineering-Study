"""Pure Pareto analysis for explicit loop-engineering objectives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ObjectivePoint:
    strategy: str
    success_rate: float
    total_cost: float
    average_success_steps: float | None


def _steps(point: ObjectivePoint) -> float:
    return point.average_success_steps if point.average_success_steps is not None else float("inf")


def dominates(left: ObjectivePoint, right: ObjectivePoint) -> bool:
    no_worse = (
        left.success_rate >= right.success_rate
        and left.total_cost <= right.total_cost
        and _steps(left) <= _steps(right)
    )
    strictly_better = (
        left.success_rate > right.success_rate
        or left.total_cost < right.total_cost
        or _steps(left) < _steps(right)
    )
    return no_worse and strictly_better


def pareto_front(points: Sequence[ObjectivePoint]) -> tuple[ObjectivePoint, ...]:
    return tuple(point for point in points if not any(other != point and dominates(other, point) for other in points))


def dominated_by(points: Sequence[ObjectivePoint]) -> dict[str, list[str]]:
    return {point.strategy: [other.strategy for other in points if dominates(other, point)] for point in points if any(dominates(other, point) for other in points)}
