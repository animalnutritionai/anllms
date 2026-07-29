"""
Validation tests for calcium requirement equations, checked against real
fixture cases from tests/nasem_unit_testing/micronutrient_requirement_equations_test.json
in animalnutritionai/NASEM-Model-Python.
"""

import math

import pytest

from anllms.scientific.minerals.calcium import (
    CalciumGestationNASEM2021,
    CalciumGrowthNASEM2021,
    CalciumMaintenanceNASEM2021,
    CalciumRequirementNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_maintenance_matches_fixture():
    # {'An_DMIn': 25} -> 22.5
    result = CalciumMaintenanceNASEM2021().calculate(dmi_kg=25)
    assert math.isclose(result.value, 22.5, rel_tol=1e-9)


def test_growth_matches_fixture():
    # {'An_BW_mature': 750, 'An_BW': 684, 'Body_Gain': 0.6} -> 6.0187444470346145
    result = CalciumGrowthNASEM2021().calculate(bw_mature_kg=750, bw_kg=684, body_gain_kg_per_day=0.6)
    assert math.isclose(result.value, 6.0187444470346145, rel_tol=1e-9)


def test_gestation_matches_fixture():
    # {'An_GestDay': 129, 'An_BW': 783} -> 0.4158712230667302
    result = CalciumGestationNASEM2021().calculate(gestation_day=129, bw_kg=783)
    assert math.isclose(result.value, 0.4158712230667302, rel_tol=1e-9)


def test_lactation_matches_book_formula_directly():
    # (0.295 + 0.239*3.9) * 30 = 36.813, matches fixture
    # {'Mlk_NP_g': 1240, 'Ca_Mlk': 3.8, 'Trg_MilkProd': 30, 'Trg_MilkTPp': 3.9} -> 36.812999999999995
    import nasem_dairy as nd
    value = nd.calculate_An_Ca_l(Mlk_NP_g=1240, Ca_Mlk=3.8, Trg_MilkProd=30, Trg_MilkTPp=3.9)
    assert math.isclose(value, 36.812999999999995, rel_tol=1e-9)


def test_total_requirement_is_sum_of_components():
    result = CalciumRequirementNASEM2021().calculate(
        dmi_kg=22, bw_mature_kg=700, bw_kg=650, body_gain_kg_per_day=0,
        gestation_day=0, milk_yield_kg=38, milk_true_protein_pct=3.2,
    )
    maintenance = CalciumMaintenanceNASEM2021().calculate(dmi_kg=22).value
    growth = CalciumGrowthNASEM2021().calculate(bw_mature_kg=700, bw_kg=650, body_gain_kg_per_day=0).value
    gestation = CalciumGestationNASEM2021().calculate(gestation_day=0, bw_kg=650).value
    assert math.isclose(growth, 0.0, abs_tol=1e-9)
    # Gestation Ca is a difference-of-exponentials rate curve, not an
    # on/off switch -- it does NOT evaluate to exactly zero at day 0,
    # only very close to it. Confirmed against the equation itself, not assumed.
    assert abs(gestation) < 0.01
    assert math.isclose(result.value, maintenance + growth + gestation + (
        (0.295 + 0.239 * 3.2) * 38
    ), rel_tol=1e-6)


def test_rejects_negative_dmi():
    with pytest.raises(ValueError):
        CalciumMaintenanceNASEM2021().calculate(dmi_kg=-5)


def test_explanation_has_citation():
    result = CalciumMaintenanceNASEM2021().calculate(dmi_kg=22)
    explanation = result.explain()
    assert "Equation 20-373" in explanation
