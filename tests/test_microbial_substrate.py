"""
Validation tests for feed_library.microbial_substrate, checked against
nasem_dairy's own full nd.nasem() model run on the 'lactating_cow_test'
demo scenario (not invented numbers) -- confirms the independent
diet-level pipeline agrees with the full model's own An_RDPIn, An_RDP,
Rum_DigNDFIn, and Rum_DigStIn.
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.feed_library.microbial_substrate import compute_microbial_substrate

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def _demo_ration_and_animal_input():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])
    return ration, animal_input, equation_selection


def test_matches_full_model_rdp_and_rumen_digestion_values():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)

    ration, animal_input, equation_selection = _demo_ration_and_animal_input()
    result = compute_microbial_substrate(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )

    assert math.isclose(
        result.an_rdpin_kg, expected_output.get_value("An_RDPIn"), rel_tol=1e-6
    )
    assert math.isclose(
        result.an_rdp_pct, expected_output.get_value("An_RDP"), rel_tol=1e-6
    )
    assert math.isclose(
        result.rum_digndfin_kg,
        expected_output.get_value("Rum_DigNDFIn"),
        rel_tol=1e-6,
    )
    assert math.isclose(
        result.rum_digstin_kg,
        expected_output.get_value("Rum_DigStIn"),
        rel_tol=1e-6,
    )


def test_feeds_directly_into_microbial_crude_protein_matching_full_model():
    """
    Confirms the practical point of this module: feeding its output
    straight into MicrobialCrudeProteinNASEM2021 (unchanged, already-cited
    equation) reproduces the full model's own Du_MiCP_g -- i.e. the gap
    documented in that equation's known_discrepancies is actually closed.
    """
    import nasem_dairy as nd

    from anllms.scientific.protein.microbial_crude_protein import (
        MicrobialCrudeProteinNASEM2021,
    )

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)

    ration, animal_input, equation_selection = _demo_ration_and_animal_input()
    substrate = compute_microbial_substrate(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )

    micp_result = MicrobialCrudeProteinNASEM2021().calculate(
        rdp_intake_kg=substrate.an_rdpin_kg,
        diet_rdp_pct=substrate.an_rdp_pct,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        rumen_digested_ndf_kg=substrate.rum_digndfin_kg,
        rumen_digested_starch_kg=substrate.rum_digstin_kg,
    )

    assert math.isclose(
        micp_result.value, expected_output.get_value("Du_MiCP_g"), rel_tol=1e-6
    )


def test_rejects_unknown_ingredient():
    ration = Ration()
    ration.add("Not A Real Feed", 20.0)

    with pytest.raises(ValueError, match="not found"):
        compute_microbial_substrate(ration=ration, dmi_kg=22.0)


def test_rejects_non_positive_dmi():
    ration = Ration.guelph_base_diet()

    with pytest.raises(ValueError, match="positive"):
        compute_microbial_substrate(ration=ration, dmi_kg=0.0)


def test_dt_rupin_matches_rup_supply_module():
    """
    Confirms this module's reused Dt_RUPIn (used to derive Dt_RDPIn =
    Dt_CPIn - Dt_RUPIn) matches feed_library.rup_supply's own Dt_RUPIn --
    guards against two slightly different RUP numbers ever coexisting in
    the same report.
    """
    from anllms.feed_library.rup_supply import compute_rup_supply

    ration, animal_input, equation_selection = _demo_ration_and_animal_input()

    substrate = compute_microbial_substrate(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )
    rup_result = compute_rup_supply(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )

    assert math.isclose(substrate.dt_rupin_kg, rup_result.dt_rupin_kg, rel_tol=1e-9)
