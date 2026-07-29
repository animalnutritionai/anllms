"""
Validation tests for magnesium requirement equations, checked against
real fixture cases from micronutrient_requirement_equations_test.json.
"""

import math

import pytest

from anllms.scientific.minerals.magnesium import (
    MagnesiumGestationNASEM2021,
    MagnesiumGrowthNASEM2021,
    MagnesiumLactationNASEM2021,
    MagnesiumMaintenanceNASEM2021,
    MagnesiumRequirementNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_maintenance_matches_fixtures():
    # Ur_Mg_m: {'An_BW': 784} -> 0.5488; Fe_Mg_m: {'An_DMIn': 34} -> 10.2
    result = MagnesiumMaintenanceNASEM2021().calculate(bw_kg=784, dmi_kg=34)
    assert math.isclose(result.value, 0.5488 + 10.2, rel_tol=1e-6)


def test_growth_matches_fixture():
    # {'Body_Gain': 3.7} -> 1.665
    result = MagnesiumGrowthNASEM2021().calculate(body_gain_kg_per_day=3.7)
    assert math.isclose(result.value, 1.665, rel_tol=1e-9)


def test_gestation_is_exactly_zero_before_day_190():
    # {'An_GestDay': 130, 'An_BW': 762} -> 0
    result = MagnesiumGestationNASEM2021().calculate(gestation_day=130, bw_kg=762)
    assert result.value == 0


def test_gestation_matches_fixture_after_day_190():
    # {'An_GestDay': 200, 'An_BW': 762} -> 0.3197202797
    result = MagnesiumGestationNASEM2021().calculate(gestation_day=200, bw_kg=762)
    assert math.isclose(result.value, 0.3197202797, rel_tol=1e-9)


def test_lactation_matches_fixture():
    # {'Trg_MilkProd': 32.7} -> 3.597
    result = MagnesiumLactationNASEM2021().calculate(milk_yield_kg=32.7)
    assert math.isclose(result.value, 3.597, rel_tol=1e-9)


def test_total_requirement_is_sum_of_components():
    result = MagnesiumRequirementNASEM2021().calculate(
        bw_kg=650, dmi_kg=22, body_gain_kg_per_day=0, gestation_day=0, milk_yield_kg=38,
    )
    maintenance = MagnesiumMaintenanceNASEM2021().calculate(bw_kg=650, dmi_kg=22).value
    lactation = MagnesiumLactationNASEM2021().calculate(milk_yield_kg=38).value
    assert math.isclose(result.value, maintenance + 0 + 0 + lactation, rel_tol=1e-9)


def test_gestation_known_discrepancy_documented():
    """
    Confirms the equation-number uncertainty is documented in the
    explanation, so a reader isn't misled into thinking it's confirmed.
    """
    result = MagnesiumGestationNASEM2021().calculate(gestation_day=200, bw_kg=762)
    explanation = result.explain()
    assert "not confirmed" in explanation.lower() or "extraction gap" in explanation.lower()
