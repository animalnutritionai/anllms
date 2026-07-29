"""
Validation tests for WaterRequirementLactatingNASEM2021.

Two kinds of check here, deliberately:
1. Pass-through arithmetic against the raw unit-test fixture (whatever
   scale that fixture happened to use for Dt_DM).
2. A REAL scenario, using percentage-scale Dt_DM as confirmed against an
   actual full nasem_dairy model run -- this is the check that would have
   caught this file's earlier incorrect "must be a 0-1 fraction"
   assumption, which was wrong (see module docstring's CORRECTION note).
"""

import math

import pytest

from anllms.scientific.water.water_requirement import WaterRequirementLactatingNASEM2021

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_matches_isolated_fixture_pass_through():
    # {'An_StatePhys': 'Lactating Cow', 'Dt_DMIn': 24, 'Dt_DM': 0.68,
    #  'Dt_Na': 2.5, 'Dt_K': 1.2, 'Dt_CP': 14.9, 'Env_TempCurr': 25}
    # -> 122.20402742474917
    # NOTE: this fixture's Dt_DM=0.68 is very likely a synthetic test
    # value, not a realistic diet DM percentage -- see the next test for
    # a realistic-scale check.
    result = WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=24, diet_dm_pct=0.68, diet_na_pct=2.5, diet_k_pct=1.2,
        diet_cp_pct=14.9, ambient_temp_c=25,
    )
    assert math.isclose(result.value, 122.20402742474917, rel_tol=1e-9)


def test_matches_real_full_model_run_with_percentage_scale_dm():
    """
    Confirms our wrapper reproduces the REAL reference model's own
    An_WaIn output when given the model's own (percentage-scale)
    Dt_DM/Dt_Na/Dt_K/Dt_CP values directly -- this is the check that
    would have caught the earlier incorrect fraction assumption.
    """
    import nasem_dairy as nd

    user_diet_df, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )
    expected_output = nd.nasem(user_diet_df, animal_input, equation_selection)
    expected_wain = expected_output.get_value("An_WaIn")

    result = WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=expected_output.get_value("Dt_DMIn"),
        diet_dm_pct=expected_output.get_value("Dt_DM"),
        diet_na_pct=expected_output.get_value("Dt_Na"),
        diet_k_pct=expected_output.get_value("Dt_K"),
        diet_cp_pct=expected_output.get_value("Dt_CP"),
        ambient_temp_c=animal_input["Env_TempCurr"],
    )
    assert math.isclose(result.value, expected_wain, rel_tol=1e-6)
    # Sanity: a realistic lactating cow should need on the order of
    # 80-150 kg/d water, not a value in the single digits or thousands.
    assert 50 < result.value < 200


def test_rejects_dm_outside_plausible_percentage_range():
    with pytest.raises(ValueError, match="PERCENTAGE"):
        WaterRequirementLactatingNASEM2021().calculate(
            dmi_kg=24, diet_dm_pct=150, diet_na_pct=0.3, diet_k_pct=1.2,
            diet_cp_pct=16, ambient_temp_c=25,
        )


def test_rejects_nonpositive_dmi():
    with pytest.raises(ValueError):
        WaterRequirementLactatingNASEM2021().calculate(
            dmi_kg=0, diet_dm_pct=65, diet_na_pct=0.3, diet_k_pct=1.2,
            diet_cp_pct=16, ambient_temp_c=25,
        )


def test_higher_temperature_increases_water_requirement():
    cool = WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=24, diet_dm_pct=65, diet_na_pct=0.3, diet_k_pct=1.2,
        diet_cp_pct=16, ambient_temp_c=10,
    )
    hot = WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=24, diet_dm_pct=65, diet_na_pct=0.3, diet_k_pct=1.2,
        diet_cp_pct=16, ambient_temp_c=30,
    )
    assert hot.value > cool.value


def test_explanation_flags_lactating_only_scope():
    result = WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=24, diet_dm_pct=65, diet_na_pct=0.3, diet_k_pct=1.2,
        diet_cp_pct=16, ambient_temp_c=25,
    )
    explanation = result.explain()
    assert "Equation 9-1" in explanation
    assert "Heifers and dry cows" in explanation
