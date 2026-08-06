"""
Validation tests for GestationMPRequirementNASEM2021 and
GestationNELRequirementNASEM2021.

The 'lactating_cow_test' demo scenario has An_GestDay=46 (pregnant),
so it's a real test case for nonzero gestation requirements.
"""

import math

import pytest

from anllms.scientific.energy.gestation_energy import GestationNELRequirementNASEM2021
from anllms.scientific.protein.gestation_mp import GestationMPRequirementNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_gest_mp_matches_isolated_fixture_math():
    # {'Gest_NPuse_g': 582, coeff_dict None(->0.33)} -> 1763.6363636363635
    import nasem_dairy as nd
    value = nd.calculate_Gest_MPUse_g_Trg(Gest_NPuse_g=582, coeff_dict={"Ky_MP_NP_Trg": 0.33})
    assert math.isclose(value, 1763.6363636363635, rel_tol=1e-9)


def test_gest_nel_matches_isolated_fixture_math():
    # {'Gest_MEuse': 317, coeff_dict None(->0.66)} -> 209.22
    import nasem_dairy as nd
    value = nd.calculate_Gest_NELuse(Gest_MEuse=317, coeff_dict={"Kl_ME_NE": 0.66})
    assert math.isclose(value, 209.22, rel_tol=1e-9)


def test_gest_mp_matches_real_pregnant_cow_scenario():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    assert animal_input["An_GestDay"] > 0  # confirm this scenario really is pregnant
    model_output = nd.nasem(user_diet_df, animal_input, equation_selection)

    result = GestationMPRequirementNASEM2021().calculate(model_output=model_output)
    expected = model_output.Requirements["protein"]["Gest_MPUse_g_Trg"]
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert result.value > 0  # pregnant cow, should be nonzero
    assert result.unit == "g/d"


def test_gest_nel_matches_real_pregnant_cow_scenario():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    model_output = nd.nasem(user_diet_df, animal_input, equation_selection)

    result = GestationNELRequirementNASEM2021().calculate(model_output=model_output)
    expected = model_output.Requirements["energy"]["Gest_NELuse"]
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert result.value > 0
    assert result.unit == "Mcal/d"


def test_gest_mp_explanation_documents_scope_gap():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    model_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    result = GestationMPRequirementNASEM2021().calculate(model_output=model_output)
    explanation = result.explain()
    assert "Equation 20-239" in explanation
    assert "GrUter" in explanation


def test_gest_nel_explanation_documents_software_deprecation_note():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    model_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    result = GestationNELRequirementNASEM2021().calculate(model_output=model_output)
    explanation = result.explain()
    assert "Equation 20-237" in explanation
    assert "should not be used" in explanation.lower()
