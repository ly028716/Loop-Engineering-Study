"""Public typing contract for observable loop decisions."""

from typing import get_type_hints

from loop_engineering.evaluators import Evaluation
from loop_engineering.policies import Decision


def test_decision_parameters_support_named_observable_values() -> None:
    assert get_type_hints(Decision)["parameters"] == dict[str, object]


def test_evaluation_signals_support_named_observable_values() -> None:
    assert get_type_hints(Evaluation)["signals"] == dict[str, object]
