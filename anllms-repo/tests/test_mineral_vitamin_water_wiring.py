"""
Tests for simulation.mineral_vitamin_water and its wiring into
RequirementsReport.
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget
from anllms.simulation.mineral_vitamin_water import (
    compute_mineral_balances,
    compute_mineral_results,
    compute_vitamin_balances,
    compute_vitamin_results,
    compute_water_result,
)
from anllms.simulation.nasem_model_bridge import run_full_model
from anllms.simulation.requirements_report import build_requirements_report

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")

ALL_MINERAL_SYMBOLS = {"Ca", "P", "Mg", "Na", "Cl", "K", "S", "Co", "Cu", "Fe", "Mn", "Se", "Zn", "I"}
ALL_VITAMIN_SYMBOLS = {"A", "D", "E"}


@pytest.fixture
def typical_cow():
    animal = AnimalState(bw_kg=650, bcs=3.0, days_in_milk=150, parity=2)
    milk = MilkTarget(yield_kg=38, fat_pct=3.8, true_protein_pct=3.2, lactose_pct=4.8)
    ration = Ration()
    ration.add("Alfalfa meal", 8.0)
    ration.add("Canola meal", 5.0)
    ration.add("Corn silage, typical", 12.0)
    ration.add("Corn grain HM, coarse grind", 3.0)
    return animal, milk, ration


def test_compute_mineral_results_covers_all_13_minerals(typical_cow):
    animal, milk, ration = typical_cow
    results = compute_mineral_results(animal, milk, dmi_kg=22.0)
    assert set(results.keys()) == ALL_MINERAL_SYMBOLS
    for symbol, result in results.items():
        assert result.value > 0, f"{symbol} requirement should be positive"


def test_compute_mineral_balances_present_for_all_minerals(typical_cow):
    animal, milk, ration = typical_cow
    model_output = run_full_model(animal, milk, ration, dmi_kg=22.0)
    balances = compute_mineral_balances(model_output)
    assert set(balances.keys()) == ALL_MINERAL_SYMBOLS


def test_compute_vitamin_results_covers_a_d_e(typical_cow):
    animal, milk, ration = typical_cow
    results = compute_vitamin_results(animal, milk)
    assert set(results.keys()) == ALL_VITAMIN_SYMBOLS
    for symbol, result in results.items():
        assert result.value > 0


def test_water_result_matches_reference_models_own_an_wain(typical_cow):
    """
    Confirms compute_water_result reproduces the reference model's own
    An_WaIn exactly -- this is the check that would have caught (and did
    catch, during development) an earlier incorrect Dt_DM percent-to-
    fraction conversion that was silently wrong.
    """
    animal, milk, ration = typical_cow
    model_output = run_full_model(animal, milk, ration, dmi_kg=22.0)
    result = compute_water_result(dmi_kg=22.0, model_output=model_output)
    expected = model_output.get_value("An_WaIn")
    assert math.isclose(result.value, expected, rel_tol=1e-6)


def test_requirements_report_includes_minerals_vitamins_water(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    assert set(report.mineral_results.keys()) == ALL_MINERAL_SYMBOLS
    assert set(report.mineral_balances.keys()) == ALL_MINERAL_SYMBOLS
    assert set(report.vitamin_results.keys()) == ALL_VITAMIN_SYMBOLS
    assert report.water_result.value > 0


def test_requirements_report_summary_includes_mineral_and_vitamin_lines(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    summary = report.summary()
    assert "Ca:" in summary
    assert "Vit" in summary or "A: req" in summary
    assert "Water requirement" in summary


def test_mineral_and_vitamin_requirements_still_individually_explainable(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    ca_explanation = report.mineral_results["Ca"].explain()
    assert "20-373" in ca_explanation or "20-376" in ca_explanation

    vite_explanation = report.vitamin_results["E"].explain()
    assert "20-495" in vite_explanation
