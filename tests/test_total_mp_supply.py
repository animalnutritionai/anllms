"""
Validation tests for TotalMPSupplyNASEM2021, checked against
nasem_dairy's own 'lactating_cow_test' demo scenario output directly
(not invented numbers).
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.scientific.protein.total_mp_supply import TotalMPSupplyNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_matches_demo_scenario_directly():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    expected_total_g = (
        expected_output.get_value("Du_idMiTP_g")
        + expected_output.get_value("Dt_idRUPIn") * 1000
    )

    animal = AnimalState(
        bw_kg=animal_input["An_BW"],
        bcs=animal_input["An_BCS"],
        days_in_milk=animal_input["An_LactDay"],
        parity=animal_input["An_Parity_rl"],
        bw_mature_kg=animal_input["An_BW_mature"],
        gestation_day=animal_input["An_GestDay"],
        gestation_length_day=animal_input["An_GestLength"],
        calf_birth_weight_kg=animal_input["Fet_BWbrth"],
        age_day=int(animal_input["An_AgeDay"]),
        breed=animal_input["An_Breed"],
        age_at_dry_feed_start_day=animal_input["An_AgeDryFdStart"],
        frame_gain_kg_per_day=animal_input["Trg_FrmGain"],
        reserve_gain_kg_per_day=animal_input["Trg_RsrvGain"],
        env_temp_c=animal_input["Env_TempCurr"],
        env_distance_to_parlor_m=animal_input["Env_DistParlor"],
        env_trips_to_parlor=animal_input["Env_TripsParlor"],
        env_topography_code=animal_input["Env_Topo"],
    )
    milk = MilkTarget(
        yield_kg=animal_input["Trg_MilkProd"],
        fat_pct=animal_input["Trg_MilkFatp"],
        true_protein_pct=animal_input["Trg_MilkTPp"],
        lactose_pct=animal_input["Trg_MilkLacp"],
    )
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = TotalMPSupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=animal_input["Trg_Dt_DMIn"]
    )

    assert math.isclose(result.value, expected_total_g, rel_tol=1e-6)
    assert result.unit == "g/d"


def test_rejects_unknown_ingredient_before_running_model():
    animal = AnimalState(bw_kg=650, bcs=3, days_in_milk=150, parity=2)
    milk = MilkTarget(yield_kg=38, fat_pct=3.8, true_protein_pct=3.2, lactose_pct=4.8)
    ration = Ration()
    ration.add("Not A Real Feed", 20.0)

    with pytest.raises(ValueError, match="not found"):
        TotalMPSupplyNASEM2021().calculate(animal=animal, milk=milk, ration=ration, dmi_kg=22.0)


def test_explanation_states_scope_decision():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    animal = AnimalState(
        bw_kg=animal_input["An_BW"], bcs=animal_input["An_BCS"],
        days_in_milk=animal_input["An_LactDay"], parity=animal_input["An_Parity_rl"],
    )
    milk = MilkTarget(
        yield_kg=animal_input["Trg_MilkProd"], fat_pct=animal_input["Trg_MilkFatp"],
        true_protein_pct=animal_input["Trg_MilkTPp"], lactose_pct=animal_input["Trg_MilkLacp"],
    )
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = TotalMPSupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=animal_input["Trg_Dt_DMIn"]
    )
    explanation = result.explain()
    assert "independently" in explanation.lower()
    assert "full nasem_dairy.nasem() model run" in explanation or "full model run" in explanation.lower()
