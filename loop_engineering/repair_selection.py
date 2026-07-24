"""Deterministic ranking for completed repair candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .metrics import MetricReport


@dataclass(frozen=True)
class RepairCandidateEvaluation:
    """Evidence collected from one fully rerun repair candidate."""

    name: str
    declaration_index: int
    succeeded: bool
    target_diagnostics_eliminated: bool
    metrics: MetricReport
    diagnostic_codes: tuple[str, ...]
    artifact_path: str


@dataclass(frozen=True)
class RepairSelection:
    """The best candidate and the stable rule that selected it."""

    selected: RepairCandidateEvaluation
    reason: str


def _rank_key(candidate: RepairCandidateEvaluation) -> tuple[object, ...]:
    return (
        not candidate.succeeded,
        not candidate.target_diagnostics_eliminated,
        candidate.metrics.cost,
        candidate.metrics.steps,
        candidate.declaration_index,
    )


def rank_repair_candidates(
    candidates: Sequence[RepairCandidateEvaluation],
) -> tuple[RepairCandidateEvaluation, ...]:
    """Rank candidates by success, diagnostics, cost, steps, then declaration order."""

    return tuple(sorted(candidates, key=_rank_key))


def select_best_repair(
    candidates: Sequence[RepairCandidateEvaluation],
) -> RepairSelection:
    """Select the best declared candidate from completed rerun evidence."""

    ranked = rank_repair_candidates(candidates)
    if not ranked:
        raise ValueError("At least one repair candidate is required.")
    return RepairSelection(
        selected=ranked[0],
        reason=(
            "Selected by success, target diagnostic elimination, cost, steps, "
            "and declaration order."
        ),
    )


__all__ = [
    "RepairCandidateEvaluation",
    "RepairSelection",
    "rank_repair_candidates",
    "select_best_repair",
]
