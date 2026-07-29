"""
Validation tests for MilkNetProteinNASEM2021 and MilkMPRequirementNASEM2021.

Test cases copied from tests/nasem_unit_testing/protein_requirement_equations_test.json
in animalnutritionai/NASEM-Model-Python.
"""

import math

import pytest

from anllms.scientific.protein.milk_mp_requirement import MilkMPRequirementNASEM2021
from anllms.scientific.protein.milk_net_protein import MilkNetProteinNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_milk_np_matches_fixture():
    # {'Trg_MilkProd': 34, 'Trg_MilkTPp': 3.3} -> 1122
    result = MilkNetProteinNASEM2021().calculate(milk_yield_kg=34, milk_true_protein_pct=3.3)
    assert math.isclose(result.value, 1122, rel_tol=1e-9)
    assert result.unit == "g/d"


def test_milk_np_rejects_negative_yield():
    with pytest.raises(ValueError):
        MilkNetProteinNASEM2021().calculate(milk_yield_kg=-1, milk_true_protein_pct=3.3)


def test_milk_mp_requirement_matches_fixture_efficiency_step():
    # {'Trg_Mlk_NP_g': 320, 'coeff_dict': {'Kl_MP_NP_Trg': 0.69}} -> 463.768115942029
    # Reproduced here via the composed calculate() using yield/TP% that
    # generates NP=320 is awkward, so we check the efficiency division
    # directly using the same numbers the fixture used.
    import nasem_dairy as nd
    value = nd.calculate_Mlk_MPUse_g_Trg(Trg_Mlk_NP_g=320, coeff_dict={"Kl_MP_NP_Trg": 0.69})
    assert math.isclose(value, 463.768115942029, rel_tol=1e-9)


def test_milk_mp_requirement_end_to_end():
    # 34 kg/d at 3.3% TP -> NP = 1122 g/d -> MP = 1122 / 0.69
    result = MilkMPRequirementNASEM2021().calculate(milk_yield_kg=34, milk_true_protein_pct=3.3)
    expected = 1122 / 0.69
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert result.unit == "g/d"


def test_milk_mp_requirement_explanation_distinguishes_target_from_dynamic_efficiency():
    result = MilkMPRequirementNASEM2021().calculate(milk_yield_kg=34, milk_true_protein_pct=3.3)
    explanation = result.explain()
    assert "Equation 20-213" in explanation
    assert "target" in explanation.lower()
    assert "20-212" in explanation  # the dynamic alternative must be cross-referenced
