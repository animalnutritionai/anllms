"""
Validation tests for feed_library.rup_supply, checked against
nasem_dairy's own full nd.nasem() model run on the 'lactating_cow_test'
demo scenario (not invented numbers) -- confirms the independent
per-feed-pipeline path agrees with the full model's Dt_idRUPIn.
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.feed_library.rup_supply import compute_rup_supply

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_matches_full_model_dt_idrupin():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    expected_dt_idrupin_kg = expected_output.get_value("Dt_idRUPIn")

    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = compute_rup_supply(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )

    assert math.isclose(result.dt_idrupin_kg, expected_dt_idrupin_kg, rel_tol=1e-6)


def test_per_feed_breakdown_sums_to_diet_total():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = compute_rup_supply(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
        use_dndf_iv=equation_selection["Use_DNDF_IV"],
    )

    assert set(result.fd_idrupin_kg.keys()) == set(ration.feedstuffs)
    assert math.isclose(
        sum(result.fd_idrupin_kg.values()), result.dt_idrupin_kg, rel_tol=1e-9
    )
    assert set(result.fd_rupin_kg.keys()) == set(ration.feedstuffs)
    assert math.isclose(
        sum(result.fd_rupin_kg.values()), result.dt_rupin_kg, rel_tol=1e-9
    )


def test_rejects_unknown_ingredient():
    ration = Ration()
    ration.add("Not A Real Feed", 20.0)

    with pytest.raises(ValueError, match="not found"):
        compute_rup_supply(ration=ration, dmi_kg=22.0)


def test_rejects_non_positive_dmi():
    ration = Ration.guelph_base_diet()

    with pytest.raises(ValueError, match="positive"):
        compute_rup_supply(ration=ration, dmi_kg=0.0)
