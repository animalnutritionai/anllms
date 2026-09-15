"""
Validation tests for feed_library.mineral_vitamin_supply, checked against
nasem_dairy's own full nd.nasem() model run on the 'lactating_cow_test'
demo scenario (not invented numbers) -- confirms the independent
per-feed-pipeline path agrees with the full model's own Abs_*In/Dt_*In
values, the same way test_rup_supply.py verifies Dt_idRUPIn.
"""

import math

import pytest

from anllms.feed_library.mineral_vitamin_supply import compute_mineral_vitamin_supply
from anllms.feed_library.ration import Ration

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")

_EXPECTED_KEYS = [
    "Abs_CaIn", "Abs_PIn", "Abs_MgIn", "Abs_NaIn", "Abs_KIn", "Abs_ClIn",
    "Abs_CoIn", "Abs_CuIn", "Abs_FeIn", "Abs_MnIn", "Abs_ZnIn",
    "Dt_SIn", "Dt_IIn", "Dt_SeIn",
    "Dt_VitAIn", "Dt_VitDIn", "Dt_VitEIn",
]


@pytest.fixture(scope="module")
def scenario():
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)

    ration = Ration()
    for _, row in user_diet_df.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    result = compute_mineral_vitamin_supply(
        ration=ration,
        dmi_kg=animal_input["Trg_Dt_DMIn"],
        an_state_phys=animal_input["An_StatePhys"],
    )
    return result, expected_output


def test_all_17_supply_values_match_full_model(scenario):
    result, expected_output = scenario
    assert set(result.keys()) == set(_EXPECTED_KEYS)
    for key in _EXPECTED_KEYS:
        expected = expected_output.get_value(key)
        assert math.isclose(result[key], expected, rel_tol=1e-6), (
            f"{key}: independent={result[key]!r} vs full-model={expected!r}"
        )
