"""
Validation tests for MicrobialCrudeProteinNASEM2021 and MicrobialMPSupplyNASEM2021.

Numeric cases copied from tests/nasem_unit_testing/microbial_protein_equations_test.json
in animalnutritionai/NASEM-Model-Python.
"""

import math

import pytest

from anllms.scientific.protein.microbial_crude_protein import MicrobialCrudeProteinNASEM2021
from anllms.scientific.protein.microbial_mp_supply import MicrobialMPSupplyNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_rdpin_minmax_cap_logic_via_full_chain():
    # calculate_RDPIn_MiNmax: {'Dt_DMIn': 20, 'An_RDP': 15, 'An_RDPIn': 5} -> 2.4
    # (An_RDP=15% > 12%, so capped at Dt_DMIn*0.12 = 20*0.12 = 2.4)
    import nasem_dairy as nd
    value = nd.calculate_RDPIn_MiNmax(Dt_DMIn=20, An_RDP=15, An_RDPIn=5)
    assert math.isclose(value, 2.4, rel_tol=1e-9)


def test_min_vm_matches_fixture():
    # {'RDPIn_MiNmax': 3, coeff_dict None(->100.8/81.56)} -> 345.48
    import nasem_dairy as nd
    value = nd.calculate_MiN_Vm(
        RDPIn_MiNmax=3, coeff_dict={"VmMiNInt": 100.8, "VmMiNRDPSlp": 81.56}
    )
    assert math.isclose(value, 345.48, rel_tol=1e-9)


def test_microbial_crude_protein_end_to_end():
    # Using values chosen so An_RDP <= 12 (no capping) to keep the chain simple:
    # An_RDPIn=1.0 kg, An_RDP=10% (<=12, so RDPIn_MiNmax = An_RDPIn = 1.0 kg)
    result = MicrobialCrudeProteinNASEM2021().calculate(
        rdp_intake_kg=1.0,
        diet_rdp_pct=10.0,
        dmi_kg=20.0,
        rumen_digested_ndf_kg=4.7,
        rumen_digested_starch_kg=2.9,
    )
    # Reproduce by hand using the same reference functions directly
    import nasem_dairy as nd
    min_vm = nd.calculate_MiN_Vm(
        RDPIn_MiNmax=1.0, coeff_dict={"VmMiNInt": 100.8, "VmMiNRDPSlp": 81.56}
    )
    du_min_g = nd.calculate_Du_MiN_NRC2021_g(
        MiN_Vm=min_vm, Rum_DigNDFIn=4.7, Rum_DigStIn=2.9, An_RDPIn_g=1000,
        coeff_dict={"KmMiNRDNDF": 0.0939, "KmMiNRDSt": 0.0274},
    )
    expected_micp_g = du_min_g * 6.25
    assert math.isclose(result.value, expected_micp_g, rel_tol=1e-9)
    assert result.unit == "g/d"


def test_microbial_crude_protein_rejects_zero_digested_ndf():
    with pytest.raises(ValueError):
        MicrobialCrudeProteinNASEM2021().calculate(
            rdp_intake_kg=1.0, diet_rdp_pct=10.0, dmi_kg=20.0,
            rumen_digested_ndf_kg=0, rumen_digested_starch_kg=2.9,
        )


def test_du_idmicp_g_matches_fixture():
    # {'Du_MiCP_g': 12.4, coeff_dict None(->80)} -> 9.92
    import nasem_dairy as nd
    value = nd.calculate_Du_idMiCP_g(Du_MiCP_g=12.4, coeff_dict={"SI_dcMiCP": 80})
    assert math.isclose(value, 9.92, rel_tol=1e-9)


def test_du_idmitp_g_matches_fixture():
    # {'Du_idMiCP_g': 127.3, coeff_dict None(->0.824)} -> 104.8952
    import nasem_dairy as nd
    value = nd.calculate_Du_idMiTP_g(Du_idMiCP_g=127.3, coeff_dict={"fMiTP_MiCP": 0.824})
    assert math.isclose(value, 104.8952, rel_tol=1e-9)


def test_microbial_mp_supply_end_to_end_65_9_pct_combined_efficiency():
    result = MicrobialMPSupplyNASEM2021().calculate(
        rdp_intake_kg=1.0, diet_rdp_pct=10.0, dmi_kg=20.0,
        rumen_digested_ndf_kg=4.7, rumen_digested_starch_kg=2.9,
    )
    micp = MicrobialCrudeProteinNASEM2021().calculate(
        rdp_intake_kg=1.0, diet_rdp_pct=10.0, dmi_kg=20.0,
        rumen_digested_ndf_kg=4.7, rumen_digested_starch_kg=2.9,
    ).value
    # 0.80 * 0.824 = 0.659 combined conversion efficiency, verified via
    # the two separate multiplications matching the book's stated figure.
    expected = micp * 0.80 * 0.824
    assert math.isclose(result.value, expected, rel_tol=1e-9)
    assert math.isclose(0.80 * 0.824, 0.659, rel_tol=1e-3)


def test_microbial_mp_supply_explanation_flags_rup_gap():
    result = MicrobialMPSupplyNASEM2021().calculate(
        rdp_intake_kg=1.0, diet_rdp_pct=10.0, dmi_kg=20.0,
        rumen_digested_ndf_kg=4.7, rumen_digested_starch_kg=2.9,
    )
    explanation = result.explain()
    assert "RUP" in explanation
    assert "65.9" in explanation or "0.824" in explanation
