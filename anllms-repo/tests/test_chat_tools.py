"""
Tests for chat.tools.ChatSession -- confirms the tool layer correctly
wraps existing, already-tested anllms functionality. Does NOT test the
Claude API loop itself (that needs a real API key and is exercised
manually, not in CI).
"""

import pytest

from chat.tools import ChatSession

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


def test_search_feed_ingredient():
    session = ChatSession()
    result = session.dispatch("search_feed_ingredient", {"query": "canola"})
    assert "matches" in result
    assert any("canola" in m.lower() for m in result["matches"])


def test_calculate_requirements_returns_headline_numbers():
    session = ChatSession()
    result = session.dispatch("calculate_lactating_cow_requirements", {
        "bw_kg": 650, "bcs": 3.0, "days_in_milk": 150, "parity": 2,
        "milk_yield_kg": 38, "milk_fat_pct": 3.8, "milk_true_protein_pct": 3.2,
        "milk_lactose_pct": 4.8,
        "ration_items": [
            {"name": "Alfalfa meal", "kg_dm_per_day": 8.0},
            {"name": "Canola meal", "kg_dm_per_day": 5.0},
            {"name": "Corn silage, typical", "kg_dm_per_day": 12.0},
            {"name": "Corn grain HM, coarse grind", "kg_dm_per_day": 3.0},
        ],
    })
    assert "error" not in result
    assert result["dmi_kg_per_day"] > 0
    assert result["mp_requirement_g_per_day"] > 0
    assert "Eq." in result["dmi_equation_used"]


def test_calculate_requirements_rejects_unknown_ingredient():
    session = ChatSession()
    result = session.dispatch("calculate_lactating_cow_requirements", {
        "bw_kg": 650, "bcs": 3.0, "days_in_milk": 150, "parity": 2,
        "milk_yield_kg": 38, "milk_fat_pct": 3.8, "milk_true_protein_pct": 3.2,
        "milk_lactose_pct": 4.8,
        "ration_items": [{"name": "Not A Real Feed", "kg_dm_per_day": 10}],
    })
    assert "error" in result
    assert "Not A Real Feed" in result["error"]


def test_explain_component_without_prior_calculation_gives_clear_error():
    session = ChatSession()
    result = session.dispatch("explain_component", {"component": "mp_maintenance"})
    assert "error" in result
    assert "No requirements calculation" in result["error"]


def test_explain_component_after_calculation():
    session = ChatSession()
    session.dispatch("calculate_lactating_cow_requirements", {
        "bw_kg": 650, "bcs": 3.0, "days_in_milk": 150, "parity": 2,
        "milk_yield_kg": 38, "milk_fat_pct": 3.8, "milk_true_protein_pct": 3.2,
        "milk_lactose_pct": 4.8,
        "ration_items": [
            {"name": "Alfalfa meal", "kg_dm_per_day": 8.0},
            {"name": "Canola meal", "kg_dm_per_day": 5.0},
            {"name": "Corn silage, typical", "kg_dm_per_day": 12.0},
            {"name": "Corn grain HM, coarse grind", "kg_dm_per_day": 3.0},
        ],
    })
    result = session.dispatch("explain_component", {"component": "nel_maintenance"})
    assert "error" not in result
    assert "Equation 3-13" in result["explanation"]


def test_unknown_tool_name_returns_error():
    session = ChatSession()
    result = session.dispatch("not_a_real_tool", {})
    assert "error" in result


def test_calculate_requirements_includes_minerals_vitamins_water():
    session = ChatSession()
    result = session.dispatch("calculate_lactating_cow_requirements", {
        "bw_kg": 650, "bcs": 3.0, "days_in_milk": 150, "parity": 2,
        "milk_yield_kg": 38, "milk_fat_pct": 3.8, "milk_true_protein_pct": 3.2,
        "milk_lactose_pct": 4.8,
        "ration_items": [
            {"name": "Alfalfa meal", "kg_dm_per_day": 8.0},
            {"name": "Canola meal", "kg_dm_per_day": 5.0},
            {"name": "Corn silage, typical", "kg_dm_per_day": 12.0},
            {"name": "Corn grain HM, coarse grind", "kg_dm_per_day": 3.0},
        ],
    })
    assert result["water_requirement_kg_per_day"] > 0
    assert set(result["minerals"].keys()) == {
        "Ca", "P", "Mg", "Na", "Cl", "K", "S", "Co", "Cu", "Fe", "Mn", "Se", "Zn", "I"
    }
    assert set(result["vitamins"].keys()) == {"A", "D", "E"}
    assert result["minerals"]["Ca"]["requirement"] > 0
    assert result["vitamins"]["E"]["requirement"] > 0


def test_explain_component_handles_mineral_and_vitamin_prefixes():
    session = ChatSession()
    session.dispatch("calculate_lactating_cow_requirements", {
        "bw_kg": 650, "bcs": 3.0, "days_in_milk": 150, "parity": 2,
        "milk_yield_kg": 38, "milk_fat_pct": 3.8, "milk_true_protein_pct": 3.2,
        "milk_lactose_pct": 4.8,
        "ration_items": [
            {"name": "Alfalfa meal", "kg_dm_per_day": 8.0},
            {"name": "Canola meal", "kg_dm_per_day": 5.0},
            {"name": "Corn silage, typical", "kg_dm_per_day": 12.0},
            {"name": "Corn grain HM, coarse grind", "kg_dm_per_day": 3.0},
        ],
    })
    ca_result = session.dispatch("explain_component", {"component": "mineral_Ca"})
    assert "error" not in ca_result
    assert "20-373" in ca_result["explanation"] or "20-376" in ca_result["explanation"]

    vite_result = session.dispatch("explain_component", {"component": "vitamin_E"})
    assert "error" not in vite_result
    assert "20-495" in vite_result["explanation"]

    water_result = session.dispatch("explain_component", {"component": "water"})
    assert "error" not in water_result
    assert "Equation 9-1" in water_result["explanation"]

    unknown = session.dispatch("explain_component", {"component": "mineral_XX"})
    assert "error" in unknown
