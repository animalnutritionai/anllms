"""
Validation tests for phosphorus requirement equations, checked against
real fixture cases from micronutrient_requirement_equations_test.json.
"""

import math

import pytest

from anllms.scientific.minerals.phosphorus import (
    PhosphorusGestationNASEM2021,
    PhosphorusGrowthNASEM2021,
    PhosphorusMaintenanceNASEM2021,
    PhosphorusRequirementNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_maintenance_matches_fixtures():
    # Ur_P_m: {'An_BW': 745} -> 0.447
    # Fe_P_m heifer: {'An_Parity_rl': 0, 'An_DMIn': 18.4} -> 14.72
    # An_P_m: {'Ur_P_m': 4.9, 'Fe_P_m': 7.3} -> 12.2
    result_heifer = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=745, dmi_kg=18.4, parity=0)
    expected = 0.447 + 14.72
    assert math.isclose(result_heifer.value, expected, rel_tol=1e-6)


def test_maintenance_differs_by_parity():
    heifer = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=745, dmi_kg=18.4, parity=0)
    cow = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=745, dmi_kg=18.4, parity=2)
    # Fecal coefficient: 0.8 for heifer vs 1.0 for cow -- cow's maintenance must be higher
    assert cow.value > heifer.value


def test_growth_matches_fixture():
    # {'An_BW_mature': 750, 'An_BW': 783, 'Body_Gain': 0.4} -> 2.316519821790819
    result = PhosphorusGrowthNASEM2021().calculate(bw_mature_kg=750, bw_kg=783, body_gain_kg_per_day=0.4)
    assert math.isclose(result.value, 2.316519821790819, rel_tol=1e-9)


def test_gestation_matches_fixture():
    # {'An_GestDay': 59, 'An_BW': 712} -> 0.024921222441948256
    result = PhosphorusGestationNASEM2021().calculate(gestation_day=59, bw_kg=712)
    assert math.isclose(result.value, 0.024921222441948256, rel_tol=1e-9)


def test_lactation_uses_fraction_not_percent():
    """
    Confirms MlkNP_Milk is passed as a FRACTION (TPp/100), not the raw
    percent -- the key detail this equation depends on getting right.
    """
    import nasem_dairy as nd
    milk_yield, tp_pct = 31, 3.2
    expected = (0.48 + 0.13 * (tp_pct / 100) * 100) * milk_yield
    value = nd.calculate_An_P_l(Trg_MilkProd=milk_yield, MlkNP_Milk=tp_pct / 100)
    assert math.isclose(value, expected, rel_tol=1e-9)
    # Sanity: with realistic 3.2% protein, requirement should be a
    # plausible tens-of-grams-per-day figure, not thousands.
    assert 0 < value < 100


def test_total_requirement_is_sum_of_components():
    result = PhosphorusRequirementNASEM2021().calculate(
        bw_kg=650, dmi_kg=22, parity=2, bw_mature_kg=700,
        body_gain_kg_per_day=0, gestation_day=0,
        milk_yield_kg=38, milk_true_protein_pct=3.2,
    )
    maintenance = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=650, dmi_kg=22, parity=2).value
    growth = PhosphorusGrowthNASEM2021().calculate(bw_mature_kg=700, bw_kg=650, body_gain_kg_per_day=0).value
    gestation = PhosphorusGestationNASEM2021().calculate(gestation_day=0, bw_kg=650).value
    assert math.isclose(growth, 0.0, abs_tol=1e-9)
    lactation_expected = (0.48 + 0.13 * (3.2 / 100) * 100) * 38
    assert math.isclose(result.value, maintenance + growth + gestation + lactation_expected, rel_tol=1e-6)


def test_explanation_has_citation():
    result = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=650, dmi_kg=22, parity=2)
    explanation = result.explain()
    assert "20-384" in explanation
