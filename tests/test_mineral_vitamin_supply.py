"""
Validation tests for the mineral/vitamin SUPPLY equations. Each now reads
its value from the supply_data dict produced by
feed_library.mineral_vitamin_supply.compute_mineral_vitamin_supply()
(independently summed from the per-feed pipeline -- see
test_mineral_vitamin_supply_independent.py for that module's own
validation against a full model run) rather than a shared model_output.
This test guards against a typo in a class's own key lookup breaking
that silently.
"""

import math

import pytest

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


@pytest.fixture(scope="module")
def real_supply_data():
    import nasem_dairy as nd

    from anllms.feed_library.mineral_vitamin_supply import compute_mineral_vitamin_supply
    from anllms.feed_library.ration import Ration

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    return compute_mineral_vitamin_supply(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
    )


def _check(cls, supply_key, unit, supply_data):
    result = cls().calculate(supply_data=supply_data)
    assert math.isclose(result.value, supply_data[supply_key], rel_tol=1e-9)
    assert result.unit == unit
    return result


def test_all_mineral_and_vitamin_supply_equations_match_supply_data(real_supply_data):
    from anllms.scientific.minerals.calcium import CalciumSupplyNASEM2021
    from anllms.scientific.minerals.phosphorus import PhosphorusSupplyNASEM2021
    from anllms.scientific.minerals.magnesium import MagnesiumSupplyNASEM2021
    from anllms.scientific.minerals.sodium import SodiumSupplyNASEM2021
    from anllms.scientific.minerals.chlorine import ChlorineSupplyNASEM2021
    from anllms.scientific.minerals.potassium import PotassiumSupplyNASEM2021
    from anllms.scientific.minerals.sulfur import SulfurSupplyNASEM2021
    from anllms.scientific.minerals.cobalt import CobaltSupplyNASEM2021
    from anllms.scientific.minerals.copper import CopperSupplyNASEM2021
    from anllms.scientific.minerals.iron import IronSupplyNASEM2021
    from anllms.scientific.minerals.manganese import ManganeseSupplyNASEM2021
    from anllms.scientific.minerals.selenium import SeleniumSupplyNASEM2021
    from anllms.scientific.minerals.zinc import ZincSupplyNASEM2021
    from anllms.scientific.minerals.iodine import IodineSupplyNASEM2021
    from anllms.scientific.vitamins.vitamin_a import VitaminASupplyNASEM2021
    from anllms.scientific.vitamins.vitamin_d import VitaminDSupplyNASEM2021
    from anllms.scientific.vitamins.vitamin_e import VitaminESupplyNASEM2021

    _check(CalciumSupplyNASEM2021, "Abs_CaIn", "g/d", real_supply_data)
    _check(PhosphorusSupplyNASEM2021, "Abs_PIn", "g/d", real_supply_data)
    _check(MagnesiumSupplyNASEM2021, "Abs_MgIn", "g/d", real_supply_data)
    _check(SodiumSupplyNASEM2021, "Abs_NaIn", "g/d", real_supply_data)
    _check(ChlorineSupplyNASEM2021, "Abs_ClIn", "g/d", real_supply_data)
    _check(PotassiumSupplyNASEM2021, "Abs_KIn", "g/d", real_supply_data)
    _check(SulfurSupplyNASEM2021, "Dt_SIn", "g/d", real_supply_data)
    _check(CobaltSupplyNASEM2021, "Abs_CoIn", "mg/d", real_supply_data)
    _check(CopperSupplyNASEM2021, "Abs_CuIn", "mg/d", real_supply_data)
    _check(IronSupplyNASEM2021, "Abs_FeIn", "mg/d", real_supply_data)
    _check(ManganeseSupplyNASEM2021, "Abs_MnIn", "mg/d", real_supply_data)
    _check(SeleniumSupplyNASEM2021, "Dt_SeIn", "mg/d", real_supply_data)
    _check(ZincSupplyNASEM2021, "Abs_ZnIn", "mg/d", real_supply_data)
    _check(IodineSupplyNASEM2021, "Dt_IIn", "mg/d", real_supply_data)
    _check(VitaminASupplyNASEM2021, "Dt_VitAIn", "IU/d", real_supply_data)
    _check(VitaminDSupplyNASEM2021, "Dt_VitDIn", "IU/d", real_supply_data)
    _check(VitaminESupplyNASEM2021, "Dt_VitEIn", "IU/d", real_supply_data)
