"""
Validation tests for vitamin A, D, E requirement equations, checked
against real fixture cases from micronutrient_requirement_equations_test.json.
"""

import math

import pytest

from anllms.scientific.vitamins.vitamin_a import VitaminARequirementNASEM2021
from anllms.scientific.vitamins.vitamin_d import VitaminDRequirementNASEM2021
from anllms.scientific.vitamins.vitamin_e import VitaminERequirementNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_vitamin_a_baseline_same_at_20_and_35_kg_milk():
    # Both should give 110*601 = 66110 -- no extra allowance below/at 35 kg/d
    result_20 = VitaminARequirementNASEM2021().calculate(bw_kg=601, milk_yield_kg=20)
    result_35 = VitaminARequirementNASEM2021().calculate(bw_kg=601, milk_yield_kg=35)
    assert math.isclose(result_20.value, 66110, rel_tol=1e-9)
    assert math.isclose(result_35.value, 66110, rel_tol=1e-9)


def test_vitamin_a_extra_allowance_above_35_kg():
    # {'Trg_MilkProd': 40, 'An_BW': 601} -> 71110
    result = VitaminARequirementNASEM2021().calculate(bw_kg=601, milk_yield_kg=40)
    assert math.isclose(result.value, 71110, rel_tol=1e-9)


def test_vitamin_d_higher_when_lactating():
    dry = VitaminDRequirementNASEM2021().calculate(bw_kg=741, milk_yield_kg=0)
    lactating = VitaminDRequirementNASEM2021().calculate(bw_kg=741, milk_yield_kg=10)
    assert math.isclose(dry.value, 23712, rel_tol=1e-9)
    assert math.isclose(lactating.value, 29640, rel_tol=1e-9)
    assert lactating.value > dry.value


def test_vitamin_e_lactating_normal_gestation():
    # {'Trg_MilkProd': 20, 'Parity': 1, 'Lactating Cow', 'BW': 704,
    #  'GestDay': 200, 'Preg': 0, 'PastIn': 1.2} -> 503.2
    result = VitaminERequirementNASEM2021().calculate(
        bw_kg=704, milk_yield_kg=20, parity=1, gestation_day=200,
        is_pregnant=False, pasture_dmi_kg=1.2,
    )
    assert math.isclose(result.value, 503.20000000000005, rel_tol=1e-9)


def test_vitamin_e_close_up_override_replaces_not_adds():
    # {'Trg_MilkProd': 20, GestDay=287, Preg=1} -> 2052 = 3*704
    # (NOT 0.8*704 + 3*704 -- confirms override REPLACES the base)
    result = VitaminERequirementNASEM2021().calculate(
        bw_kg=704, milk_yield_kg=20, parity=1, gestation_day=287,
        is_pregnant=True, pasture_dmi_kg=1.2,
    )
    assert math.isclose(result.value, 2052, rel_tol=1e-9)
    assert result.value != 0.8 * 704 + 3 * 704


def test_vitamin_e_close_up_override_applies_regardless_of_lactating_status():
    """
    Same close-up scenario but explicitly 'dry' should give the identical
    result -- confirms the override doesn't care about lactating status,
    only gestation day and pregnancy.
    """
    lactating = VitaminERequirementNASEM2021().calculate(
        bw_kg=704, milk_yield_kg=20, parity=1, gestation_day=287,
        is_pregnant=True, pasture_dmi_kg=1.2,
    )
    dry = VitaminERequirementNASEM2021().calculate(
        bw_kg=704, milk_yield_kg=0, parity=1, gestation_day=287,
        is_pregnant=True, pasture_dmi_kg=1.2,
    )
    assert math.isclose(lactating.value, dry.value, rel_tol=1e-9)


def test_vitamin_e_rejects_negative_pasture_intake():
    with pytest.raises(ValueError):
        VitaminERequirementNASEM2021().calculate(
            bw_kg=704, milk_yield_kg=20, parity=1, gestation_day=200,
            is_pregnant=False, pasture_dmi_kg=-1,
        )


def test_vitamin_e_explanation_documents_override_behavior():
    result = VitaminERequirementNASEM2021().calculate(
        bw_kg=704, milk_yield_kg=20, parity=1, gestation_day=287,
        is_pregnant=True, pasture_dmi_kg=1.2,
    )
    explanation = result.explain()
    assert "REPLACES" in explanation
