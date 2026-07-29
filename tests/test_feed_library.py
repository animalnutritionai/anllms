"""
Tests for feed_library.ingredient and feed_library.ration -- the real
wrapper around animalnutritionai/NASEM-Model-Python's feed library,
replacing the earlier placeholder.
"""

import math

import pytest

from anllms.feed_library.ingredient import Ingredient, search_feed_library
from anllms.feed_library.ration import Ration

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_load_real_ingredient_corn_silage():
    ing = Ingredient.from_library("Corn silage, typical")
    assert ing.name == "Corn silage, typical"
    assert ing.is_forage is True
    assert ing.dm_pct > 0
    assert ing.cp_pct > 0
    # Real kinetics data should be present for a common ingredient
    assert ing.cp_a_fraction_pct is not None
    assert ing.cp_b_fraction_pct is not None
    assert ing.rup_intestinal_digestibility_pct is not None


def test_load_real_ingredient_canola_meal_is_not_forage():
    ing = Ingredient.from_library("Canola meal")
    assert ing.is_forage is False
    assert ing.cp_pct > 30  # canola meal is a high-protein ingredient


def test_unknown_ingredient_raises_clear_error():
    with pytest.raises(ValueError, match="not found"):
        Ingredient.from_library("Definitely Not A Real Feed XYZ")


def test_search_feed_library_finds_corn_entries():
    results = search_feed_library("corn")
    assert len(results) > 0
    assert any("corn" in r.lower() for r in results)


def test_ration_builds_correct_user_diet_shape():
    ration = Ration()
    ration.add("Alfalfa meal", 8.21)
    ration.add("Canola meal", 6.73)
    ration.add("Corn silage, typical", 5.47)
    ration.add("Corn grain HM, coarse grind", 4.11)

    df = ration.to_user_diet_df()
    assert list(df.columns) == ["Feedstuff", "kg_user"]
    assert len(df) == 4
    assert math.isclose(ration.total_dmi_kg, 8.21 + 6.73 + 5.47 + 4.11)


def test_ration_rejects_negative_inclusion():
    ration = Ration()
    with pytest.raises(ValueError):
        ration.add("Corn silage, typical", -1.0)


def test_ration_validate_feedstuffs_catches_typo():
    ration = Ration()
    ration.add("Corn silage, typical", 10.0)
    ration.add("Totally Made Up Feed", 5.0)
    missing = ration.validate_feedstuffs_exist()
    assert missing == ["Totally Made Up Feed"]


def test_ration_validate_feedstuffs_all_valid():
    ration = Ration()
    ration.add("Corn silage, typical", 10.0)
    ration.add("Canola meal", 3.0)
    missing = ration.validate_feedstuffs_exist()
    assert missing == []


def test_this_matches_the_actual_demo_scenario_composition():
    """
    Reproduces the exact ration from nasem_dairy's own
    'lactating_cow_test' demo scenario, confirming our Ration wrapper
    produces a DataFrame usable by the real nd.nasem() call.
    """
    import nasem_dairy as nd

    user_diet_expected, animal_input, equation_selection, infusion_input = nd.demo(
        "lactating_cow_test"
    )

    ration = Ration()
    for _, row in user_diet_expected.iterrows():
        ration.add(row["Feedstuff"], row["kg_user"])

    built_df = ration.to_user_diet_df()
    assert list(built_df["Feedstuff"]) == list(user_diet_expected["Feedstuff"])
    assert built_df["kg_user"].tolist() == pytest.approx(user_diet_expected["kg_user"].tolist())

    # Confirm this DataFrame actually runs through the real model without error
    output = nd.nasem(built_df, animal_input, equation_selection)
    assert output.get_value("Dt_idRUPIn") > 0
