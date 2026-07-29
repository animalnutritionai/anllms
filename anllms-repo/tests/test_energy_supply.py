"""
Validation tests for TotalEnergySupplyNASEM2021, checked against
nasem_dairy's own 'lactating_cow_test' demo scenario output directly.
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.scientific.energy.energy_supply import TotalEnergySupplyNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_matches_demo_scenario_directly():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    expected_nein = expected_output.get_value("An_NEIn")

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
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = TotalEnergySupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=animal_input["Trg_Dt_DMIn"]
    )

    assert math.isclose(result.value, expected_nein, rel_tol=1e-6)
    assert result.unit == "Mcal/d"


def test_nel_supply_equals_me_supply_times_0_66():
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

    result = TotalEnergySupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=animal_input["Trg_Dt_DMIn"]
    )
    me_supply = result.inputs_used["ME supply (Mcal/d, An_MEIn)"]
    assert math.isclose(result.value, me_supply * 0.66, rel_tol=1e-9)


def test_explanation_cites_equation_3_12_and_states_scope_gap():
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

    result = TotalEnergySupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=animal_input["Trg_Dt_DMIn"]
    )
    explanation = result.explain()
    assert "Equation 3-12" in explanation
    assert "0.66" in explanation
