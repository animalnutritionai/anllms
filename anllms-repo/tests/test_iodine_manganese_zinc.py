"""
Validation tests for iodine, manganese, and zinc requirement equations,
checked against real fixture cases from
micronutrient_requirement_equations_test.json.
"""

import math

import pytest

from anllms.scientific.minerals.iodine import IodineRequirementNASEM2021
from anllms.scientific.minerals.manganese import (
    ManganeseGestationNASEM2021,
    ManganeseLactationNASEM2021,
    ManganeseMaintenanceNASEM2021,
    ManganeseRequirementNASEM2021,
)
from anllms.scientific.minerals.zinc import (
    ZincGestationNASEM2021,
    ZincLactationNASEM2021,
    ZincMaintenanceNASEM2021,
    ZincRequirementNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_iodine_matches_fixture():
    # {'An_StatePhys': 'Lactating Cow', 'An_DMIn': 27.3, 'An_BW': 740,
    #  'Trg_MilkProd': 30} -> 10.069815808440236
    result = IodineRequirementNASEM2021().calculate(bw_kg=740, milk_yield_kg=30)
    assert math.isclose(result.value, 10.069815808440236, rel_tol=1e-9)


def test_manganese_maintenance_matches_fixture():
    result = ManganeseMaintenanceNASEM2021().calculate(bw_kg=712)
    assert math.isclose(result.value, 1.8512, rel_tol=1e-9)


def test_manganese_gestation_step_function():
    before = ManganeseGestationNASEM2021().calculate(gestation_day=40, bw_kg=673)
    after = ManganeseGestationNASEM2021().calculate(gestation_day=210, bw_kg=673)
    assert before.value == 0
    assert math.isclose(after.value, 0.28266, rel_tol=1e-9)


def test_manganese_lactation_matches_fixture():
    result = ManganeseLactationNASEM2021().calculate(milk_yield_kg=32.1)
    assert math.isclose(result.value, 0.963, rel_tol=1e-9)


def test_manganese_total_is_sum():
    result = ManganeseRequirementNASEM2021().calculate(
        bw_kg=650, body_gain_kg_per_day=0, gestation_day=0, milk_yield_kg=38
    )
    maintenance = ManganeseMaintenanceNASEM2021().calculate(bw_kg=650).value
    assert result.value > maintenance  # lactation term must add on top


def test_zinc_maintenance_matches_fixture():
    result = ZincMaintenanceNASEM2021().calculate(dmi_kg=26.2)
    assert math.isclose(result.value, 131, rel_tol=1e-9)


def test_zinc_gestation_step_function():
    before = ZincGestationNASEM2021().calculate(gestation_day=140, bw_kg=738)
    after = ZincGestationNASEM2021().calculate(gestation_day=240, bw_kg=738)
    assert before.value == 0
    assert math.isclose(after.value, 12.546, rel_tol=1e-9)


def test_zinc_lactation_matches_fixture():
    result = ZincLactationNASEM2021().calculate(milk_yield_kg=28.3)
    assert math.isclose(result.value, 113.2, rel_tol=1e-9)


def test_zinc_total_is_sum():
    result = ZincRequirementNASEM2021().calculate(
        dmi_kg=22, body_gain_kg_per_day=0, gestation_day=0, bw_kg=650, milk_yield_kg=38
    )
    maintenance = ZincMaintenanceNASEM2021().calculate(dmi_kg=22).value
    lactation = ZincLactationNASEM2021().calculate(milk_yield_kg=38).value
    assert math.isclose(result.value, maintenance + lactation, rel_tol=1e-9)
