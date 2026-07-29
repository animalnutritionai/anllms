"""
Validation tests for NEmilkPerKgNASEM2021 and LactationNELRequirementNASEM2021.

Test cases below are copied from the reference repo's own JSON fixtures
(tests/nasem_unit_testing/milk_equations_test.json in
animalnutritionai/NASEM-Model-Python), not invented, so that "correct"
means "matches their own accepted test data."
"""

import math

import pytest

from anllms.scientific.energy.lactation import LactationNELRequirementNASEM2021
from anllms.scientific.energy.milk_composition import NEmilkPerKgNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_nemilk_full_formula_3_14b_matches_fixture():
    # From milk_equations_test.json:
    # {'Trg_MilkFatp': 3.6, 'Trg_MilkTPp': 3.3, 'Trg_MilkLacp': 4.8} -> 0.71709
    result = NEmilkPerKgNASEM2021().calculate(
        milk_fat_pct=3.6, milk_true_protein_pct=3.3, milk_lactose_pct=4.8
    )
    assert math.isclose(result.value, 0.7170899999999999, rel_tol=1e-9)
    assert result.unit == "Mcal/kg milk"


def test_nemilk_fatonly_fallback_3_14c_matches_fixture():
    # From milk_equations_test.json:
    # {'Trg_MilkFatp': 3.4, 'Trg_MilkTPp': None, 'Trg_MilkLacp': None} -> 0.68946
    result = NEmilkPerKgNASEM2021().calculate(milk_fat_pct=3.4)
    assert math.isclose(result.value, 0.68946, rel_tol=1e-9)


def test_nemilk_rejects_negative_fat():
    with pytest.raises(ValueError):
        NEmilkPerKgNASEM2021().calculate(milk_fat_pct=-1)


def test_lactation_nel_composes_milk_yield_and_energy_content():
    # 30 kg/d at the 3-14b fixture composition above
    result = LactationNELRequirementNASEM2021().calculate(
        milk_yield_kg=30,
        milk_fat_pct=3.6,
        milk_true_protein_pct=3.3,
        milk_lactose_pct=4.8,
    )
    expected = 30 * 0.7170899999999999
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert result.unit == "Mcal/d"


def test_lactation_nel_rejects_negative_yield():
    with pytest.raises(ValueError):
        LactationNELRequirementNASEM2021().calculate(milk_yield_kg=-5, milk_fat_pct=3.5)


def test_lactation_nel_explanation_has_citation_and_composition_note():
    result = LactationNELRequirementNASEM2021().calculate(
        milk_yield_kg=30, milk_fat_pct=3.6, milk_true_protein_pct=3.3, milk_lactose_pct=4.8
    )
    explanation = result.explain()
    assert "Equation 20-220" in explanation
    assert "NASEM Dairy 2021" in explanation
