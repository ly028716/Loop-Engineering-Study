"""Baseline: repeat an ineffective repair until the budget stops it."""

from __future__ import annotations

if __package__:
    from ._bootstrap import persist_and_print_summary
else:
    from _bootstrap import prepare_script_imports, persist_and_print_summary

    prepare_script_imports(__file__)

from examples.code_repair.domain import (
    CandidateRepairAction,
    RepeatedCandidatePolicy,
    TestCaseEvaluator,
    boundary_repair_case,
    initial_repair_state,
)
from loop_engineering.runner import LoopRunner
from loop_engineering.stopping import MaxSteps, SuccessReached


def run():
    case = boundary_repair_case()
    return LoopRunner(
        policy=RepeatedCandidatePolicy("off_by_one"),
        action=CandidateRepairAction(case),
        evaluator=TestCaseEvaluator(case),
        stop_conditions=[SuccessReached(), MaxSteps(3)],
    ).run(initial_repair_state())


if __name__ == "__main__":
    persist_and_print_summary(run(), __file__)
