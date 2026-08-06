"""
Validation tests for the mineral/vitamin SUPPLY equations added to close
the supply citation gap. Each just extracts a real model_output value,
so the test simply confirms it matches the model's own field exactly
(these should be identical by construction, but the test guards against
a typo in the field name breaking that silently).
"""

import math

import pytest

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


@pytest.fixture(scope="module")
def real_model_output():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    return nd.nasem(user_diet_df, animal_input, equation_selection)


def _check(cls, model_key, unit, model_output):
    result = cls().calculate(model_output=model_output)
    expected = model_output.get_value(model_key)
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert result.unit == unit
    return result


def test_all_mineral_and_vitamin_supply_equations_match_model_output(real_model_output):
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

    _check(CalciumSupplyNASEM2021, "Abs_CaIn", "g/d", real_model_output)
    _check(PhosphorusSupplyNASEM2021, "Abs_PIn", "g/d", real_model_output)
    _check(MagnesiumSupplyNASEM2021, "Abs_MgIn", "g/d", real_model_output)
    _check(SodiumSupplyNASEM2021, "Abs_NaIn", "g/d", real_model_output)
    _check(ChlorineSupplyNASEM2021, "Abs_ClIn", "g/d", real_model_output)
    _check(PotassiumSupplyNASEM2021, "Abs_KIn", "g/d", real_model_output)
    _check(SulfurSupplyNASEM2021, "Dt_SIn", "g/d", real_model_output)
    _check(CobaltSupplyNASEM2021, "Abs_CoIn", "mg/d", real_model_output)
    _check(CopperSupplyNASEM2021, "Abs_CuIn", "mg/d", real_model_output)
    _check(IronSupplyNASEM2021, "Abs_FeIn", "mg/d", real_model_output)
    _check(ManganeseSupplyNASEM2021, "Abs_MnIn", "mg/d", real_model_output)
    _check(SeleniumSupplyNASEM2021, "Dt_SeIn", "mg/d", real_model_output)
    _check(ZincSupplyNASEM2021, "Abs_ZnIn", "mg/d", real_model_output)
    _check(IodineSupplyNASEM2021, "Dt_IIn", "mg/d", real_model_output)
    _check(VitaminASupplyNASEM2021, "Dt_VitAIn", "IU/d", real_model_output)
    _check(VitaminDSupplyNASEM2021, "Dt_VitDIn", "IU/d", real_model_output)
    _check(VitaminESupplyNASEM2021, "Dt_VitEIn", "IU/d", real_model_output)


def test_calcium_supply_has_real_citation(real_model_output):
    from anllms.scientific.minerals.calcium import CalciumSupplyNASEM2021
    result = CalciumSupplyNASEM2021().calculate(model_output=real_model_output)
    explanation = result.explain()
    assert "20-370" in explanation or "20-371" in explanation


def test_magnesium_supply_documents_k_inhibition(real_model_output):
    from anllms.scientific.minerals.magnesium import MagnesiumSupplyNASEM2021
    result = MagnesiumSupplyNASEM2021().calculate(model_output=real_model_output)
    explanation = result.explain()
    assert "inhibited" in explanation.lower() or "UNLIKE" in explanation
