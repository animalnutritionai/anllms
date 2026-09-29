"""
Tests for anllms.decision.solve_diet. These run the REAL nd.nasem()
model per candidate (via evaluate_diet), matching this project's
validate-against-real-data rule -- no hand-computed expected numbers.
Optimizer runs use tiny maxiter/popsize purely to keep the suite fast;
they check STRUCTURE and CORRECTNESS of the reported numbers, not that
the optimizer fully converges.
"""

import pytest

from anllms.decision.diet_request import IngredientBound, NutrientBound, ObjectiveSpec, SolveRequest
from anllms.decision.solve_diet import SolveOptions, solve_diet
from anllms.simulation.animal_state import AnimalState, MilkTarget

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")
pytest.importorskip("scipy", reason="optional dev/test-only dependency")

_CANDIDATE_FEEDS = [
    "Alfalfa meal", "Canola meal", "Corn silage, typical", "Corn grain HM, coarse grind",
]
_FAST = SolveOptions(maxiter=1, popsize=4, seed=1, polish=False)


def _animal_and_milk():
    animal = AnimalState(bw_kg=650, bcs=3.0, days_in_milk=150, parity=2)
    milk = MilkTarget(yield_kg=38, fat_pct=3.8, true_protein_pct=3.2, lactose_pct=4.8)
    return animal, milk


def _base_request(**overrides):
    animal, milk = _animal_and_milk()
    defaults = dict(
        animal=animal, milk=milk,
        objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=list(_CANDIDATE_FEEDS),
        default_max_kg_dm_per_day=15.0,
        dmi_mode="actual", known_dmi_kg=24.5,
    )
    defaults.update(overrides)
    return SolveRequest(**defaults)


def test_solve_diet_rejects_unbounded_candidate_feeds():
    animal, milk = _animal_and_milk()
    req = SolveRequest(
        animal=animal, milk=milk, objective=ObjectiveSpec(kind="feasibility_only"),
        candidate_feeds=["Alfalfa meal"],  # no default_max_kg_dm_per_day, no IngredientBound
    )
    with pytest.raises(ValueError, match="finite upper bound"):
        solve_diet(req, _FAST)


def test_solve_diet_rejects_missing_prices():
    req = _base_request(
        objective=ObjectiveSpec(kind="least_cost", feed_prices={"Alfalfa meal": 0.1}),
    )
    with pytest.raises(ValueError, match="needs a price for"):
        solve_diet(req, _FAST)


def test_solve_diet_rejects_unsupported_nutrient():
    req = _base_request(nutrient_bounds=[NutrientBound("Starch", min_value=20.0)])
    with pytest.raises(NotImplementedError, match="not a nutrient solve_diet"):
        solve_diet(req, _FAST)


def test_solve_diet_rejects_relative_bound_on_composition_only_nutrient():
    req = _base_request(nutrient_bounds=[NutrientBound("NDF", min_pct_of_requirement=100.0)])
    with pytest.raises(NotImplementedError, match="needs a default NASEM requirement"):
        solve_diet(req, _FAST)


def test_solve_diet_returns_real_evaluation_and_ration():
    req = _base_request()
    result = solve_diet(req, _FAST)

    assert result.ration.feedstuffs == _CANDIDATE_FEEDS
    assert len(result.ration.kg_dm_per_day) == len(_CANDIDATE_FEEDS)
    assert all(kg >= -1e-6 for kg in result.ration.kg_dm_per_day)  # bounds respected
    assert result.nfev > 0
    assert result.evaluation.mp.requirement > 0  # a real number came back from nd.nasem()
    assert result.objective_value == 0.0  # feasibility_only reports no cost
    assert result.iofc is None


def test_solve_diet_relative_mp_bound_uses_this_candidates_own_requirement():
    req = _base_request(nutrient_bounds=[NutrientBound("MP", min_pct_of_requirement=105.0)])
    result = solve_diet(req, _FAST)

    mp_violation = next((v for v in result.violations if v.nutrient == "MP"), None)
    if mp_violation is not None:
        # The enforced floor must be 105% of THIS ration's own MP
        # requirement (per_candidate is the default basis), not the bare
        # default requirement -- confirmed against the real value nd.nasem()
        # returned for this exact ration, not a hand-computed number.
        assert mp_violation.required == pytest.approx(result.evaluation.mp.requirement * 1.05)


def test_solve_diet_least_cost_reports_nonnegative_cost():
    req = _base_request(
        objective=ObjectiveSpec(
            kind="least_cost",
            feed_prices={f: 0.1 for f in _CANDIDATE_FEEDS},
        ),
    )
    result = solve_diet(req, _FAST)
    assert result.objective_value >= 0.0


def test_solve_diet_baseline_locked_requires_and_uses_baseline_ration():
    from anllms.feed_library.ration import Ration

    baseline = Ration.guelph_base_diet()
    req = _base_request(
        relative_floor_basis="baseline_locked",
        baseline_ration=baseline,
        nutrient_bounds=[NutrientBound("MP", min_pct_of_requirement=100.0)],
    )
    # Should not raise (baseline_ration satisfies the requirement) and
    # should actually run the baseline through the real model once.
    result = solve_diet(req, _FAST)
    assert result.nfev > 0


# --- override-ambiguity check (NutrientBound docstring's own rule) ---

def test_solve_diet_rejects_relative_min_below_100_without_override():
    req = _base_request(nutrient_bounds=[NutrientBound("MP", min_pct_of_requirement=90.0)])
    with pytest.raises(ValueError, match="ambiguous"):
        solve_diet(req, _FAST)


def test_solve_diet_accepts_relative_min_below_100_with_override():
    # override_default=True means "replace the default", so a looser
    # floor than 100% is exactly what was asked for, not ambiguous.
    req = _base_request(
        nutrient_bounds=[NutrientBound("MP", min_pct_of_requirement=90.0, override_default=True)],
    )
    result = solve_diet(req, _FAST)  # must not raise
    assert result.nfev > 0


def test_solve_diet_rejects_absolute_min_below_default_without_override():
    # 1.0 g/d is far below any real MP requirement for a lactating cow --
    # a genuine, unambiguous case of this bug pattern.
    req = _base_request(nutrient_bounds=[NutrientBound("MP", min_value=1.0)])
    with pytest.raises(ValueError, match="ambiguous"):
        solve_diet(req, _FAST)


def test_solve_diet_accepts_absolute_min_below_default_with_override():
    req = _base_request(
        nutrient_bounds=[NutrientBound("MP", min_value=1.0, override_default=True)],
    )
    result = solve_diet(req, _FAST)  # must not raise
    assert result.nfev > 0
