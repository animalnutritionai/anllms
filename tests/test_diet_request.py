"""
Tests for anllms.decision.diet_request -- the SolveRequest spec ahead of
solve_diet itself. These test validation logic only (no optimizer
exists yet); missing_feed_names() is the one method that touches the
real feed library, matching Ration.validate_feedstuffs_exist()'s
existing test pattern.
"""

import pytest

from anllms.decision.diet_request import (
    IngredientBound,
    NutrientBound,
    ObjectiveSpec,
    SolveRequest,
)
from anllms.simulation.animal_state import AnimalState, MilkTarget

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def _animal_and_milk():
    animal = AnimalState(bw_kg=650, bcs=3.0, days_in_milk=150, parity=2)
    milk = MilkTarget(yield_kg=38, fat_pct=3.8, true_protein_pct=3.2, lactose_pct=4.8)
    return animal, milk


# --- ObjectiveSpec ---

def test_feasibility_only_needs_no_prices():
    obj = ObjectiveSpec(kind="feasibility_only")
    assert obj.needs_prices() is False


def test_least_cost_needs_prices():
    obj = ObjectiveSpec(kind="least_cost", feed_prices={"Corn silage, typical": 0.08})
    assert obj.needs_prices() is True


def test_maximize_iofc_requires_milk_price():
    with pytest.raises(ValueError, match="milk_price_per_kg"):
        ObjectiveSpec(kind="maximize_iofc")


def test_unknown_objective_kind_rejected():
    with pytest.raises(ValueError, match="Unknown objective kind"):
        ObjectiveSpec(kind="maximize_milk")  # type: ignore[arg-type]


def test_negative_feed_price_rejected():
    with pytest.raises(ValueError, match="Negative feed price"):
        ObjectiveSpec(kind="least_cost", feed_prices={"Corn silage, typical": -1.0})


# --- IngredientBound ---

def test_ingredient_bound_min_exceeds_max_rejected():
    with pytest.raises(ValueError, match="exceeds max_kg_dm_per_day"):
        IngredientBound("Corn grain HM, coarse grind", min_kg_dm_per_day=5.0, max_kg_dm_per_day=2.0)


def test_ingredient_bound_negative_min_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        IngredientBound("Corn grain HM, coarse grind", min_kg_dm_per_day=-1.0)


# --- NutrientBound ---

def test_nutrient_bound_requires_min_or_max():
    with pytest.raises(ValueError, match="must specify min_value and/or max_value"):
        NutrientBound("NDF")


def test_nutrient_bound_min_exceeds_max_rejected():
    with pytest.raises(ValueError, match="exceeds max_value"):
        NutrientBound("NDF", min_value=40.0, max_value=30.0)


def test_nutrient_bound_override_default_flag_stored():
    bound = NutrientBound("Ca", min_value=30.0, override_default=True)
    assert bound.override_default is True


# --- SolveRequest ---

def test_solve_request_rejects_empty_candidate_feeds():
    animal, milk = _animal_and_milk()
    with pytest.raises(ValueError, match="cannot be empty"):
        SolveRequest(
            animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
            candidate_feeds=[],
        )


def test_solve_request_rejects_duplicate_candidate_feeds():
    animal, milk = _animal_and_milk()
    with pytest.raises(ValueError, match="duplicate"):
        SolveRequest(
            animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
            candidate_feeds=["Alfalfa meal", "Alfalfa meal"],
        )


def test_solve_request_rejects_bound_for_feed_not_in_universe():
    animal, milk = _animal_and_milk()
    with pytest.raises(ValueError, match="not in candidate_feeds"):
        SolveRequest(
            animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
            candidate_feeds=["Alfalfa meal"],
            ingredient_bounds=[IngredientBound("Canola meal", max_kg_dm_per_day=5.0)],
        )


def test_solve_request_rejects_duplicate_bounds_for_same_feed():
    animal, milk = _animal_and_milk()
    with pytest.raises(ValueError, match="more than one bound"):
        SolveRequest(
            animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
            candidate_feeds=["Alfalfa meal"],
            ingredient_bounds=[
                IngredientBound("Alfalfa meal", max_kg_dm_per_day=5.0),
                IngredientBound("Alfalfa meal", min_kg_dm_per_day=1.0),
            ],
        )


def test_solve_request_actual_dmi_mode_requires_known_dmi():
    animal, milk = _animal_and_milk()
    with pytest.raises(ValueError, match="requires known_dmi_kg"):
        SolveRequest(
            animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
            candidate_feeds=["Alfalfa meal"], dmi_mode="actual",
        )


def test_solve_request_defaults_to_predict_mode():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=["Alfalfa meal"],
    )
    assert req.dmi_mode == "predict"
    assert req.known_dmi_kg is None


def test_missing_feed_names_flags_bad_ingredient():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=["Alfalfa meal", "Not A Real Feedstuff Name"],
    )
    assert req.missing_feed_names() == ["Not A Real Feedstuff Name"]


def test_missing_feed_names_empty_when_all_valid():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=["Alfalfa meal", "Canola meal"],
    )
    assert req.missing_feed_names() == []


def test_missing_prices_empty_for_feasibility_only():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=["Alfalfa meal", "Canola meal"],
    )
    assert req.missing_prices() == []


def test_missing_prices_flags_unpriced_candidates():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk,
        objective=ObjectiveSpec(kind="least_cost", feed_prices={"Alfalfa meal": 0.15}),
        candidate_feeds=["Alfalfa meal", "Canola meal"],
    )
    assert req.missing_prices() == ["Canola meal"]
