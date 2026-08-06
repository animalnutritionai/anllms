"""
Validation test for DMIPredictionLactatingNASEM2021.

Test case copied from tests/nasem_unit_testing/DMI_equations_test.json in
animalnutritionai/NASEM-Model-Python (calculate_Dt_DMIn_Lact1).
"""

import math

import pytest

from anllms.scientific.energy.dmi_lactating import DMIPredictionLactatingNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_dmi_lact1_matches_fixture():
    # {'An_BW': 700, 'An_BCS': 3, 'An_LactDay': 160, 'An_Parity_rl': 1,
    #  'Trg_NEmilkOut': 22.5} -> 23.894448
    result = DMIPredictionLactatingNASEM2021().calculate(
        bw_kg=700,
        bcs=3,
        lactation_day=160,
        parity=1,
        target_nel_milk_output=22.5,
    )
    assert math.isclose(result.value, 23.894448, rel_tol=1e-6)
    assert result.unit == "kg/d"


def test_dmi_rejects_bcs_outside_1_to_5_scale():
    with pytest.raises(ValueError):
        DMIPredictionLactatingNASEM2021().calculate(
            bw_kg=700, bcs=7, lactation_day=160, parity=1, target_nel_milk_output=22.5
        )


def test_dmi_rejects_zero_parity():
    with pytest.raises(ValueError):
        DMIPredictionLactatingNASEM2021().calculate(
            bw_kg=700, bcs=3, lactation_day=160, parity=0, target_nel_milk_output=22.5
        )


def test_dmi_explanation_flags_lact2_gap():
    result = DMIPredictionLactatingNASEM2021().calculate(
        bw_kg=700, bcs=3, lactation_day=160, parity=1, target_nel_milk_output=22.5
    )
    explanation = result.explain()
    assert "Equation 2-1" in explanation
    assert "Lact2" in explanation  # known_discrepancies about diet-aware DMI must surface
