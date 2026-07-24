import random

import pytest

from experiments.stochastic_robustness import StochasticAction
from loop_engineering.models import LoopState
from loop_engineering.policies import Decision


def test_stochastic_action_is_reproducible_for_the_same_seed() -> None:
    decision = Decision(name="increment", parameters={"amount": 1.0})
    first = StochasticAction(0.15, 0.30, random.Random(101))
    second = StochasticAction(0.15, 0.30, random.Random(101))

    first_results = [first.apply(LoopState(0, 0.0, 6.0), decision) for _ in range(3)]
    second_results = [second.apply(LoopState(0, 0.0, 6.0), decision) for _ in range(3)]

    assert first_results == second_results


@pytest.mark.parametrize("failure_rate,noise", [(-0.01, 0.1), (1.01, 0.1), (0.1, -0.1)])
def test_stochastic_action_rejects_invalid_parameters(failure_rate: float, noise: float) -> None:
    with pytest.raises(ValueError):
        StochasticAction(failure_rate, noise, random.Random(1))


def test_robustness_matrix_is_complete_and_reproducible(tmp_path) -> None:
    from experiments.stochastic_robustness import run_stochastic_robustness

    first = run_stochastic_robustness(tmp_path / "first")
    second = run_stochastic_robustness(tmp_path / "second")

    assert len(first["runs"]) == 96
    assert len(first["summaries"]) == 12
    assert all(item["run_count"] == 8 for item in first["summaries"])
    assert [item["success"] for item in first["runs"]] == [
        item["success"] for item in second["runs"]
    ]
