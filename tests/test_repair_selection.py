from loop_engineering.metrics import MetricReport
from loop_engineering.repair_selection import (
    RepairCandidateEvaluation,
    rank_repair_candidates,
    select_best_repair,
)


def _candidate(
    name: str,
    index: int,
    *,
    succeeded: bool = True,
    eliminated: bool = True,
    cost: float = 3.0,
    steps: int = 3,
) -> RepairCandidateEvaluation:
    return RepairCandidateEvaluation(
        name=name,
        declaration_index=index,
        succeeded=succeeded,
        target_diagnostics_eliminated=eliminated,
        metrics=MetricReport(steps, 1.0, succeeded, cost, 0.0),
        diagnostic_codes=(),
        artifact_path=f"/tmp/{name}.json",
    )


def test_rank_repair_candidates_uses_declared_priority() -> None:
    ranked = rank_repair_candidates(
        (
            _candidate("failed", 0, succeeded=False, cost=0.0, steps=0),
            _candidate("diagnostic-remains", 1, eliminated=False, cost=0.0, steps=0),
            _candidate("expensive", 2, cost=5.0, steps=1),
            _candidate("slow", 3, cost=3.0, steps=5),
            _candidate("best", 4, cost=3.0, steps=3),
        )
    )

    assert [item.name for item in ranked] == [
        "best",
        "slow",
        "expensive",
        "diagnostic-remains",
        "failed",
    ]


def test_select_best_repair_preserves_declaration_order_for_exact_ties() -> None:
    selection = select_best_repair(
        (_candidate("declared-first", 0), _candidate("declared-second", 1))
    )

    assert selection.selected.name == "declared-first"
    assert "declaration order" in selection.reason
