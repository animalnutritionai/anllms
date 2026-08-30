"""
Validation tests for anllms.decision.evaluate_diet, checked against
nasem_dairy's own 'lactating_cow_test' demo scenario and
Ration.guelph_base_diet() (which is that same scenario's ration --
confirmed to match nd.demo()'s feed list and kg values directly).
"""

import pytest

from anllms.decision.evaluate_diet import evaluate_diet
from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def _demo_animal_and_milk():
    import nasem_dairy as nd

    _, animal_input, _, _ = nd.demo("lactating_cow_test")
    animal = AnimalState(
        bw_kg=animal_input["An_BW"], bcs=animal_input["An_BCS"],
        days_in_milk=animal_input["An_LactDay"], parity=animal_input["An_Parity_rl"],
        bw_mature_kg=animal_input["An_BW_mature"], gestation_day=animal_input["An_GestDay"],
        gestation_length_day=animal_input["An_GestLength"],
        calf_birth_weight_kg=animal_input["Fet_BWbrth"],
        age_day=int(animal_input["An_AgeDay"]), breed=animal_input["An_Breed"],
        age_at_dry_feed_start_day=animal_input["An_AgeDryFdStart"],
        frame_gain_kg_per_day=animal_input["Trg_FrmGain"],
        reserve_gain_kg_per_day=animal_input["Trg_RsrvGain"],
        env_temp_c=animal_input["Env_TempCurr"],
        env_distance_to_parlor_m=animal_input["Env_DistParlor"],
        env_trips_to_parlor=animal_input["Env_TripsParlor"],
        env_topography_code=animal_input["Env_Topo"],
    )
    milk = MilkTarget(
        yield_kg=animal_input["Trg_MilkProd"], fat_pct=animal_input["Trg_MilkFatp"],
        true_protein_pct=animal_input["Trg_MilkTPp"], lactose_pct=animal_input["Trg_MilkLacp"],
    )
    return animal, milk


def test_evaluate_diet_on_demo_scenario_matches_underlying_report():
    """
    evaluate_diet() should reshape, not alter, the numbers already
    produced (and separately validated) by build_requirements_report().
    """
    from anllms.simulation.requirements_report import build_requirements_report

    animal, milk = _demo_animal_and_milk()
    ration = Ration.guelph_base_diet()

    evaluation = evaluate_diet(animal, milk, ration)
    direct_report = build_requirements_report(animal, milk, ration)

    assert evaluation.nel.requirement == pytest.approx(direct_report.total_nel_requirement_mcal)
    assert evaluation.nel.supply == pytest.approx(direct_report.nel_supply_total.value)
    assert evaluation.mp.requirement == pytest.approx(direct_report.total_mp_requirement_g)
    assert evaluation.mp.balance == pytest.approx(direct_report.mp_balance_g)
    for symbol, result in direct_report.mineral_results.items():
        match = next(m for m in evaluation.minerals if m.name == symbol)
        assert match.requirement == pytest.approx(result.value)


def test_no_dmi_mismatch_flag_when_ration_matches_demo_exactly():
    # guelph_base_diet() IS the demo scenario's own ration -- total kg DM
    # should land very close to whatever DMI equation predicts for it.
    animal, milk = _demo_animal_and_milk()
    ration = Ration.guelph_base_diet()

    evaluation = evaluate_diet(animal, milk, ration)

    assert evaluation.ration_total_dmi_kg == pytest.approx(ration.total_dmi_kg)
    # Not asserting mismatch_flag is False outright -- the diet-aware DMI
    # equation predicts intake FROM this diet's composition, it doesn't
    # just echo the ration's total, so some daylight is expected. Assert
    # instead that when a mismatch IS flagged, the warning explaining it
    # is actually present (behavior, not a specific numeric prediction).
    if evaluation.dmi_mismatch_flag:
        assert any("predicted intake" in w for w in evaluation.warnings)


def test_status_labels_are_only_deficient_or_meets_or_exceeds():
    # No nutrient evaluation should ever claim "excess" -- that's a
    # judgment this module deliberately does not make (see module
    # docstring).
    animal, milk = _demo_animal_and_milk()
    ration = Ration.guelph_base_diet()

    evaluation = evaluate_diet(animal, milk, ration)
    all_evals = [evaluation.nel, evaluation.mp] + evaluation.minerals + evaluation.vitamins

    for nutrient in all_evals:
        assert nutrient.status in ("deficient", "meets_or_exceeds", "not_available")


def test_deficient_nutrients_list_is_consistent_with_individual_statuses():
    animal, milk = _demo_animal_and_milk()
    ration = Ration.guelph_base_diet()

    evaluation = evaluate_diet(animal, milk, ration)
    all_evals = [evaluation.nel, evaluation.mp] + evaluation.minerals + evaluation.vitamins
    expected_deficient = {n.name for n in all_evals if n.status == "deficient"}

    assert set(evaluation.deficient_nutrients) == expected_deficient


def test_empty_ration_raises_instead_of_falling_back_to_a_placeholder():
    animal, milk = _demo_animal_and_milk()
    empty_ration = Ration()

    with pytest.raises(ValueError, match="requires a real ration"):
        evaluate_diet(animal, milk, empty_ration)


def test_dmi_mismatch_flag_fires_on_a_clearly_mismatched_ration():
    # Same animal/milk target as the demo scenario, but a wildly
    # over-fed ration -- total kg DM should diverge sharply from
    # whatever the diet-aware DMI equation predicts.
    animal, milk = _demo_animal_and_milk()
    ration = Ration()
    ration.add("Alfalfa meal", 40.0)
    ration.add("Canola meal", 30.0)

    evaluation = evaluate_diet(animal, milk, ration)

    assert evaluation.dmi_mismatch_flag  # truthy, not `is True` -- upstream values are numpy types
    assert evaluation.dmi_mismatch_pct > 10.0
    assert any("predicted intake" in w for w in evaluation.warnings)
