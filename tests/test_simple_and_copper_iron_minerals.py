"""
Validation tests for sulfur, cobalt, copper, iron, and selenium
requirement equations, checked against real fixture cases from
micronutrient_requirement_equations_test.json.

These equation files were found already present in the repo (uncommitted)
without a clear record of their creation -- verified correct against the
book text and real fixture data before being trusted, and before being
tested here. See conversation history for the verification process,
which also caught a citation error in a fresh re-derivation attempt for
copper (the existing file was right; the fresh attempt was wrong).
"""

import math

import pytest

from anllms.scientific.minerals.cobalt import CobaltRequirementNASEM2021
from anllms.scientific.minerals.copper import (
    CopperGestationNASEM2021,
    CopperLactationNASEM2021,
    CopperMaintenanceNASEM2021,
    CopperRequirementNASEM2021,
)
from anllms.scientific.minerals.iron import (
    IronGestationNASEM2021,
    IronLactationNASEM2021,
    IronRequirementNASEM2021,
)
from anllms.scientific.minerals.selenium import SeleniumRequirementNASEM2021
from anllms.scientific.minerals.sulfur import SulfurRequirementNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_sulfur_matches_fixture():
    result = SulfurRequirementNASEM2021().calculate(dmi_kg=19.4)
    assert math.isclose(result.value, 38.8, rel_tol=1e-9)


def test_cobalt_matches_fixture():
    result = CobaltRequirementNASEM2021().calculate(dmi_kg=26.5)
    assert math.isclose(result.value, 5.3, rel_tol=1e-9)


def test_selenium_matches_fixture():
    result = SeleniumRequirementNASEM2021().calculate(dmi_kg=24.8)
    assert math.isclose(result.value, 7.44, rel_tol=1e-9)


def test_copper_maintenance_matches_fixture():
    # {'An_BW': 729} -> 10.5705
    result = CopperMaintenanceNASEM2021().calculate(bw_kg=729)
    assert math.isclose(result.value, 10.5705, rel_tol=1e-9)


def test_copper_gestation_three_tier_step_function():
    # day 80 -> 0, day 150 -> 0.2145 (mid-tier), day 200 -> 1.6445 (high-tier)
    low = CopperGestationNASEM2021().calculate(gestation_day=80, bw_kg=715)
    mid = CopperGestationNASEM2021().calculate(gestation_day=150, bw_kg=715)
    high = CopperGestationNASEM2021().calculate(gestation_day=200, bw_kg=715)
    assert low.value == 0
    assert math.isclose(mid.value, 0.2145, rel_tol=1e-9)
    assert math.isclose(high.value, 1.6445, rel_tol=1e-9)
    assert low.value < mid.value < high.value


def test_copper_lactation_matches_fixture():
    result = CopperLactationNASEM2021().calculate(milk_yield_kg=38.2)
    assert math.isclose(result.value, 1.528, rel_tol=1e-9)


def test_copper_total_is_sum():
    result = CopperRequirementNASEM2021().calculate(
        bw_kg=729, body_gain_kg_per_day=0, gestation_day=0, milk_yield_kg=38.2
    )
    maintenance = CopperMaintenanceNASEM2021().calculate(bw_kg=729).value
    lactation = CopperLactationNASEM2021().calculate(milk_yield_kg=38.2).value
    assert math.isclose(result.value, maintenance + lactation, rel_tol=1e-9)


def test_iron_has_no_maintenance_component():
    """
    Confirms iron's total requirement is exactly zero for a dry,
    non-pregnant, non-growing cow -- the real, confirmed absence of a
    maintenance term for this mineral, not a bug.
    """
    result = IronRequirementNASEM2021().calculate(
        body_gain_kg_per_day=0, gestation_day=0, bw_kg=650, milk_yield_kg=0
    )
    assert result.value == 0


def test_iron_gestation_matches_fixture():
    # {'An_GestDay': 250, 'An_BW': 718} -> 17.95
    result = IronGestationNASEM2021().calculate(gestation_day=250, bw_kg=718)
    assert math.isclose(result.value, 17.95, rel_tol=1e-9)


def test_iron_lactation_matches_fixture():
    result = IronLactationNASEM2021().calculate(milk_yield_kg=28.6)
    assert math.isclose(result.value, 28.6, rel_tol=1e-9)


def test_all_reject_invalid_dmi():
    with pytest.raises(ValueError):
        SulfurRequirementNASEM2021().calculate(dmi_kg=0)
    with pytest.raises(ValueError):
        CobaltRequirementNASEM2021().calculate(dmi_kg=-1)
    with pytest.raises(ValueError):
        SeleniumRequirementNASEM2021().calculate(dmi_kg=0)
