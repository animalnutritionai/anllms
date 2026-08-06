"""
Validation tests for the MP maintenance equation chain: urinary endogenous,
scurf, fecal endogenous, and the composed total.

Numeric cases copied from tests/nasem_unit_testing/{urine,protein,fecal,
protein_requirement}_equations_test.json in animalnutritionai/NASEM-Model-Python.
"""

import math

import pytest

from anllms.scientific.protein.fecal_endogenous_mp import FecalEndogenousMPNASEM2021
from anllms.scientific.protein.mp_maintenance import MPMaintenanceRequirementNASEM2021
from anllms.scientific.protein.scurf_mp import ScurfMPNASEM2021
from anllms.scientific.protein.urinary_endogenous_mp import UrinaryEndogenousMPNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_urinary_endogenous_mp_matches_fixture():
    # calculate_Ur_Nend_g: {'An_BW': 650} -> 34.45
    # calculate_Ur_NPend_g: {..., 'An_BW': 650, 'Ur_Nend_g': 167} -> 1043.75 (uses given Ur_Nend_g, not chained)
    # We chain naturally: Ur_Nend_g=34.45 -> Ur_NPend_g=34.45*6.25=215.3125 -> Ur_MPendUse_g=215.3125
    result = UrinaryEndogenousMPNASEM2021().calculate(bw_kg=650)
    assert math.isclose(result.value, 34.45 * 6.25, rel_tol=1e-9)
    assert result.unit == "g/d"


def test_scurf_mp_matches_fixture_chain():
    # calculate_Scrf_CP_g: {'An_BW': 782, 'An_StatePhys': 'Lactating Cow'} -> 10.8881488
    # calculate_Scrf_NP_g: {'Scrf_CP_g': 7, coeff_dict None(->0.86)} -> 6.02  (confirms 0.86 default)
    result = ScurfMPNASEM2021().calculate(bw_kg=782)
    expected_cp = 10.8881488
    expected_np = expected_cp * 0.86
    expected_mp = expected_np / 0.69
    assert math.isclose(result.value, expected_mp, rel_tol=1e-6)


def test_fecal_endogenous_mp_matches_fixture_chain():
    # calculate_Fe_CPend_g (Heifer branch used since it's the non-calf, non-liquid-diet
    # formula the adult 'Lactating Cow' path also uses): {'An_NDF': 5, 'Dt_DMIn': 4.67} -> 58.842
    result = FecalEndogenousMPNASEM2021().calculate(dmi_kg=4.67, diet_ndf_pct=5)
    expected_cpend = 58.842
    expected_npend = expected_cpend * 0.73
    expected_mp = expected_npend / 0.69
    assert math.isclose(result.value, expected_mp, rel_tol=1e-6)


def test_an_mpm_g_trg_matches_fixture():
    # calculate_An_MPm_g_Trg: {'Fe_MPendUse_g_Trg': 2.6, 'Scrf_MPUse_g_Trg': 7.1,
    #  'Ur_MPendUse_g': 1.9} -> 11.6
    import nasem_dairy as nd
    value = nd.calculate_An_MPm_g_Trg(
        Fe_MPendUse_g_Trg=2.6, Scrf_MPUse_g_Trg=7.1, Ur_MPendUse_g=1.9
    )
    assert math.isclose(value, 11.6, rel_tol=1e-9)


def test_mp_maintenance_composes_all_three_components():
    result = MPMaintenanceRequirementNASEM2021().calculate(
        bw_kg=650, dmi_kg=22, diet_ndf_pct=30
    )
    fecal = FecalEndogenousMPNASEM2021().calculate(dmi_kg=22, diet_ndf_pct=30).value
    scurf = ScurfMPNASEM2021().calculate(bw_kg=650).value
    urinary = UrinaryEndogenousMPNASEM2021().calculate(bw_kg=650).value
    assert math.isclose(result.value, fecal + scurf + urinary, rel_tol=1e-9)


def test_mp_maintenance_explanation_flags_both_discrepancies():
    result = MPMaintenanceRequirementNASEM2021().calculate(
        bw_kg=650, dmi_kg=22, diet_ndf_pct=30
    )
    explanation = result.explain()
    assert "Equation 20-304" in explanation or "Equation 20-305" in explanation
    assert "nonproductive" in explanation.lower() or "maintenance" in explanation.lower()
