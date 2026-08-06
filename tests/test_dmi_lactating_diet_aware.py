"""
Validation tests for DMIPredictionLactatingDietAwareNASEM2021.

Numeric case copied from tests/nasem_unit_testing/DMI_equations_test.json
(calculate_Dt_DMIn_Lact2). The >60 DIM enforcement test checks a
restriction found directly in the NASEM (2021) primary text that is NOT
enforced by the bare reference-software function itself.
"""

import math

import pytest

from anllms.scientific.energy.dmi_lactating_diet_aware import (
    DMIPredictionLactatingDietAwareNASEM2021,
)

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_dmi_lact2_matches_fixture():
    # {'Dt_ForNDF': 33.2, 'Dt_ADF': 23.5, 'Dt_NDF': 47.7,
    #  'Dt_ForDNDF48_ForNDF': 53.6, 'Trg_MilkProd': 32} -> 21.196067766457023
    result = DMIPredictionLactatingDietAwareNASEM2021().calculate(
        diet_forage_ndf_pct=33.2,
        diet_adf_pct=23.5,
        diet_ndf_pct=47.7,
        forage_ndf_digestibility_pct=53.6,
        milk_yield_kg=32,
        days_in_milk=120,  # >60, valid range; not part of the original fixture
    )
    assert math.isclose(result.value, 21.196067766457023, rel_tol=1e-9)
    assert result.unit == "kg/d"


def test_dmi_lact2_rejects_early_lactation_per_book_restriction():
    """
    The reference software function itself has no DIM parameter at all and
    would happily compute a number for a fresh cow. The book explicitly
    says this equation is not valid before 60 DIM. Our wrapper enforces
    that restriction even though the underlying function doesn't.
    """
    with pytest.raises(ValueError, match="60"):
        DMIPredictionLactatingDietAwareNASEM2021().calculate(
            diet_forage_ndf_pct=33.2,
            diet_adf_pct=23.5,
            diet_ndf_pct=47.7,
            forage_ndf_digestibility_pct=53.6,
            milk_yield_kg=32,
            days_in_milk=30,
        )


def test_dmi_lact2_rejects_zero_ndf():
    with pytest.raises(ValueError):
        DMIPredictionLactatingDietAwareNASEM2021().calculate(
            diet_forage_ndf_pct=33.2,
            diet_adf_pct=23.5,
            diet_ndf_pct=0,
            forage_ndf_digestibility_pct=53.6,
            milk_yield_kg=32,
            days_in_milk=120,
        )


def test_dmi_lact2_explanation_states_holstein_and_dim_restrictions():
    result = DMIPredictionLactatingDietAwareNASEM2021().calculate(
        diet_forage_ndf_pct=33.2,
        diet_adf_pct=23.5,
        diet_ndf_pct=47.7,
        forage_ndf_digestibility_pct=53.6,
        milk_yield_kg=32,
        days_in_milk=120,
    )
    explanation = result.explain()
    assert "Equation 2-2" in explanation
    assert "Holstein" in explanation
    assert "60 DIM" in explanation or "60 days" in explanation
