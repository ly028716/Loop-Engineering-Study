from loop_engineering.multi_objective import ObjectivePoint, dominates, pareto_front


def test_dominates_requires_no_worse_and_one_strictly_better_objective() -> None:
    best = ObjectivePoint("best", 1.0, 4.0, 3.0)
    worse = ObjectivePoint("worse", 0.8, 5.0, 4.0)

    assert dominates(best, worse) is True
    assert dominates(worse, best) is False


def test_pareto_front_keeps_non_dominated_and_identical_points() -> None:
    points = (
        ObjectivePoint("tradeoff-success", 1.0, 8.0, 5.0),
        ObjectivePoint("tradeoff-cost", 0.8, 4.0, 3.0),
        ObjectivePoint("dominated", 0.8, 6.0, 4.0),
        ObjectivePoint("identical", 0.8, 4.0, 3.0),
        ObjectivePoint("none-steps", 0.8, 4.0, None),
    )

    assert [item.strategy for item in pareto_front(points)] == [
        "tradeoff-success", "tradeoff-cost", "identical"
    ]
    assert dominates(ObjectivePoint("numeric", 0.8, 4.0, 3.0), points[-1]) is True
