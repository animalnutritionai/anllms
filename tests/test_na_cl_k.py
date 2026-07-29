"""
Validation tests for sodium, chlorine, and potassium requirement
equations, checked against real fixture cases from
micronutrient_requirement_equations_test.json.
"""

import math

import pytest

from anllms.scientific.minerals.chlorine import (
    ChlorineGestationNASEM2021,
    ChlorineLactationNASEM2021,
    ChlorineMaintenanceNASEM2021,
    ChlorineRequirementNASEM2021,
)
from anllms.scientific.minerals.potassium import (
    PotassiumGestationNASEM2021,
    PotassiumMaintenanceNASEM2021,
    PotassiumRequirementNASEM2021,
)
from anllms.scientific.minerals.sodium import (
    SodiumGestationNASEM2021,
    SodiumLactationNASEM2021,
    SodiumMaintenanceNASEM2021,
    SodiumRequirementNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


# --- Sodium ---

def test_na_maintenance_matches_fixture():
    result = SodiumMaintenanceNASEM2021().calculate(dmi_kg=26.3)
    assert math.isclose(result.value, 38.135, rel_tol=1e-9)


def test_na_gestation_zero_before_190_nonzero_after():
    before = SodiumGestationNASEM2021().calculate(gestation_day=100, bw_kg=683)
    after = SodiumGestationNASEM2021().calculate(gestation_day=200, bw_kg=683)
    assert before.value == 0
    assert math.isclose(after.value, 1.3373426573426572, rel_tol=1e-9)


def test_na_lactation_matches_fixture():
    result = SodiumLactationNASEM2021().calculate(milk_yield_kg=30.8)
    assert math.isclose(result.value, 12.32, rel_tol=1e-9)


def test_na_total_is_sum():
    result = SodiumRequirementNASEM2021().calculate(
        dmi_kg=22, body_gain_kg_per_day=0, gestation_day=0, bw_kg=650, milk_yield_kg=38,
    )
    maintenance = SodiumMaintenanceNASEM2021().calculate(dmi_kg=22).value
    lactation = SodiumLactationNASEM2021().calculate(milk_yield_kg=38).value
    assert math.isclose(result.value, maintenance + lactation, rel_tol=1e-9)


# --- Chlorine ---

def test_cl_maintenance_matches_fixture():
    result = ChlorineMaintenanceNASEM2021().calculate(dmi_kg=37)
    assert math.isclose(result.value, 41.07, rel_tol=1e-9)


def test_cl_gestation_zero_before_190_nonzero_after():
    before = ChlorineGestationNASEM2021().calculate(gestation_day=90, bw_kg=764)
    after = ChlorineGestationNASEM2021().calculate(gestation_day=200, bw_kg=764)
    assert before.value == 0
    assert math.isclose(after.value, 1.068531469, rel_tol=1e-6)


def test_cl_lactation_matches_fixture():
    result = ChlorineLactationNASEM2021().calculate(milk_yield_kg=42.1)
    assert math.isclose(result.value, 42.1, rel_tol=1e-9)


def test_cl_total_is_sum():
    result = ChlorineRequirementNASEM2021().calculate(
        dmi_kg=22, body_gain_kg_per_day=0, gestation_day=0, bw_kg=650, milk_yield_kg=38,
    )
    maintenance = ChlorineMaintenanceNASEM2021().calculate(dmi_kg=22).value
    lactation = ChlorineLactationNASEM2021().calculate(milk_yield_kg=38).value
    assert math.isclose(result.value, maintenance + lactation, rel_tol=1e-9)


# --- Potassium ---

def test_k_maintenance_matches_fixture_lactating():
    # Ur_K_m lactating: {'Trg_MilkProd': 36, 'An_BW': 739} -> 147.8
    # Fe_K_m: {'An_DMIn': 17.5} -> 43.75
    result = PotassiumMaintenanceNASEM2021().calculate(milk_yield_kg=36, bw_kg=739, dmi_kg=17.5)
    assert math.isclose(result.value, 147.8 + 43.75, rel_tol=1e-9)


def test_k_maintenance_lower_when_not_lactating():
    # Ur_K_m dry: {'Trg_MilkProd': 0, 'An_BW': 739} -> 51.73
    lactating = PotassiumMaintenanceNASEM2021().calculate(milk_yield_kg=36, bw_kg=739, dmi_kg=17.5)
    dry = PotassiumMaintenanceNASEM2021().calculate(milk_yield_kg=0, bw_kg=739, dmi_kg=17.5)
    assert dry.value < lactating.value
    assert math.isclose(dry.value, 51.73 + 43.75, rel_tol=1e-9)


def test_k_gestation_zero_before_190_nonzero_after():
    before = PotassiumGestationNASEM2021().calculate(gestation_day=100, bw_kg=793)
    after = PotassiumGestationNASEM2021().calculate(gestation_day=200, bw_kg=793)
    assert before.value == 0
    assert math.isclose(after.value, 1.142363636, rel_tol=1e-6)


def test_k_total_is_sum():
    result = PotassiumRequirementNASEM2021().calculate(
        milk_yield_kg=38, bw_kg=650, dmi_kg=22, body_gain_kg_per_day=0, gestation_day=0,
    )
    maintenance = PotassiumMaintenanceNASEM2021().calculate(milk_yield_kg=38, bw_kg=650, dmi_kg=22).value
    assert result.value > maintenance  # lactation term must add on top
