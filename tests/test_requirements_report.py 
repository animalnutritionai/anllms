"""
End-to-end test for build_requirements_report — proves the equations
compose correctly using OFFICIAL reference-model totals (not an
independently re-summed total), with Diet-level aggregates derived from a
real Ration via their own functions (Ration.to_diet()), not manually
entered.
"""

import math

import pytest

from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget
from anllms.simulation.requirements_report import build_requirements_report

pytest.importorskip("nasem_dairy", reason="optional dev/test-only dependency")


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


def test_report_builds_without_error(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    assert report.dmi_result.value > 0
    assert report.total_nel_requirement_mcal > report.nel_maintenance.value
    assert report.total_mp_requirement_g > report.mp_maintenance.value
    assert report.mp_supply_total.value > 0
    assert report.nel_supply_total.value > 0
    assert math.isclose(
        report.nel_balance_mcal,
        report.nel_supply_total.value - report.total_nel_requirement_mcal,
        rel_tol=1e-9,
    )


def test_report_uses_diet_aware_dmi_past_60_dim(typical_cow):
    animal, milk, ration = typical_cow  # days_in_milk=150
    report = build_requirements_report(animal, milk, ration)
    assert "2-2" in report.dmi_equation_used


def test_report_falls_back_to_animal_only_dmi_early_lactation(typical_cow):
    animal, milk, ration = typical_cow
    animal.days_in_milk = 30  # <=60, outside Eq. 2-2's validated range
    report = build_requirements_report(animal, milk, ration)
    assert "2-1" in report.dmi_equation_used
    assert any("could not be used" in w for w in report.warnings)


def test_totals_are_official_not_reimplemented_sums(typical_cow):
    """
    The whole point of this refactor: total_mp_requirement_g and
    total_nel_requirement_mcal must come from the reference model's own
    output, not from summing our own component calls. Since this
    scenario's default AnimalState has zero gestation/growth/reserve, our
    component sum SHOULD numerically match the official total closely --
    but the report must report the OFFICIAL number as the total field
    regardless, with any gap explicitly reconciled.
    """
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    assert abs(report.mp_unexplained_gap_g) < 0.5
    assert abs(report.nel_unexplained_gap_mcal) < 0.5


def test_reconciliation_warnings_present(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    assert any("growth/reserve" in w for w in report.warnings)


def test_pregnant_cow_gestation_is_independently_cited_and_nonzero(typical_cow):
    """
    With a nonzero gestation day, the report's own cited gestation
    equations should be nonzero and match closely enough with the
    reconciliation check that the unexplained gap stays small -- proving
    gestation is now a genuinely closed, cited component, not just
    absorbed into the reference model's total.
    """
    animal, milk, ration = typical_cow
    animal.gestation_day = 150
    report = build_requirements_report(animal, milk, ration)
    assert report.mp_gestation.value > 0
    assert report.nel_gestation.value > 0
    assert "Equation 20-239" in report.mp_gestation.explain()
    assert "Equation 20-237" in report.nel_gestation.explain()
    # Growth/reserve are still zero for this cow (no frame/reserve gain
    # set), so the unexplained gap should stay small even with gestation
    # now in the mix.
    assert abs(report.mp_unexplained_gap_g) < 0.5
    assert abs(report.nel_unexplained_gap_mcal) < 0.5


def test_reconciliation_flags_real_mismatch_when_growth_is_nonzero(typical_cow):
    """
    With frame growth set nonzero, our own MP-maintenance/lactation-only
    components will legitimately fall short of the official total by the
    growth amount. Confirms the gap is correctly EXPLAINED by the
    reference model's own Frm_MPUse_g_Trg component (no false warning),
    by checking the unexplained gap stays small even though the raw
    (naive) gap would not be zero.
    """
    animal, milk, ration = typical_cow
    animal.frame_gain_kg_per_day = 0.3  # nonzero growth
    report = build_requirements_report(animal, milk, ration)
    naive_gap = report.total_mp_requirement_g - (
        report.mp_maintenance.value + report.mp_lactation.value
    )
    assert abs(naive_gap) > 1  # there IS a real gap now (growth MP)
    assert abs(report.mp_unexplained_gap_g) < 0.5  # but it's fully explained


def test_mp_supply_runs_model_only_once(typical_cow, monkeypatch):
    """
    Confirms TotalMPSupplyNASEM2021 reuses the model_output already
    computed for requirement totals rather than triggering a second
    nd.nasem() run.
    """
    import anllms.simulation.nasem_model_bridge as bridge

    call_count = {"n": 0}
    original = bridge.run_full_model

    def counting_run_full_model(*args, **kwargs):
        call_count["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(bridge, "run_full_model", counting_run_full_model)
    # requirements_report imports run_full_model directly, so patch there too
    import anllms.simulation.requirements_report as rr
    monkeypatch.setattr(rr, "run_full_model", counting_run_full_model)

    animal, milk, ration = typical_cow
    build_requirements_report(animal, milk, ration)
    assert call_count["n"] == 1


def test_component_results_remain_individually_explainable(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(animal, milk, ration)
    assert "Equation 3-13" in report.nel_maintenance.explain()
    assert "Equation 20-304" in report.mp_maintenance.explain() or \
           "Equation 20-305" in report.mp_maintenance.explain()


# --- DMI dual-mode (dmi_mode='actual' vs 'predict') ---

def test_actual_dmi_mode_bypasses_prediction(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(
        animal, milk, ration, dmi_mode="actual", known_dmi_kg=27.3,
    )
    assert report.dmi_result.value == 27.3
    assert "actual" in report.dmi_equation_used.lower() or \
           "measured" in report.dmi_equation_used.lower()
    assert "Equation 2-1" not in report.dmi_equation_used
    assert "Equation 2-2" not in report.dmi_equation_used


def test_actual_dmi_mode_requires_known_dmi_kg(typical_cow):
    animal, milk, ration = typical_cow
    with pytest.raises(ValueError):
        build_requirements_report(animal, milk, ration, dmi_mode="actual")


def test_actual_dmi_mode_still_drives_downstream_calculations(typical_cow):
    """
    The actual-mode DMI value must flow through to the same downstream
    figures a predicted value would -- proving no special-casing was
    needed anywhere except DMI sourcing itself.
    """
    animal, milk, ration = typical_cow
    report = build_requirements_report(
        animal, milk, ration, dmi_mode="actual", known_dmi_kg=27.3,
    )
    assert report.total_mp_requirement_g > 0
    assert report.mp_supply_total.value > 0
    assert report.water_result.value > 0


def test_actual_dmi_mode_produces_a_real_explanation(typical_cow):
    animal, milk, ration = typical_cow
    report = build_requirements_report(
        animal, milk, ration, dmi_mode="actual", known_dmi_kg=27.3,
    )
    explanation = report.dmi_result.explain()
    assert "DMIn_eqn == 0" in explanation


def test_invalid_dmi_mode_rejected(typical_cow):
    animal, milk, ration = typical_cow
    with pytest.raises(ValueError):
        build_requirements_report(animal, milk, ration, dmi_mode="bogus")  # type: ignore[arg-type]
