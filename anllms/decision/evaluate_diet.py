"""
Diet evaluation -- given a REAL, already-specified ration, report whether
it meets NASEM (2021) requirements for a lactating dairy cow.

LAYERING: this file is part of anllms.decision (see
anllms/decision/__init__.py for the layering rule). It imports FROM
anllms.simulation.requirements_report -- it does not duplicate any of
that module's calculation logic, and nothing in anllms.simulation,
anllms.scientific, anllms.feed_library, or anllms.knowledge is allowed
to import back from here (enforced by tests/test_import_boundaries.py).

WHAT THIS ADDS ON TOP OF requirements_report.build_requirements_report():
  1. Requires a real ration -- no silent fallback to a placeholder demo
     diet. A specialist evaluating an actual client ration should get a
     hard error if no ration was given, not a plausible-looking report
     for the wrong diet. (The existing no-ration-given fallback behavior
     stays exactly as-is for the general/reference-lookup chat tool --
     this function is simply never used for that case.)
  2. Flags a mismatch between the ration's own total kg DM/d and the
     DMI value the model actually used to drive supply/balance
     calculations (see DMI_MISMATCH_WARNING_THRESHOLD_PCT below). This
     is a real NASEM-modeling subtlety -- predicted intake, not the
     entered ration's own total, drives every downstream number -- that
     a specialist needs surfaced explicitly, not buried in a generic
     warnings list.
  3. Reshapes every requirement/supply pair into a specialist-scannable
     per-nutrient evaluation: % of requirement met, plus a status label,
     with a top-level list of which nutrients are short.

WHAT THIS DELIBERATELY DOES NOT DO:
  - Does not define an "excess" threshold. Balance and % of requirement
    are reported as-is; whether a surplus is a problem for a given
    nutrient (toxicity, cost, or interaction concerns) is NOT modeled
    here and would need its own citation-backed basis before being
    presented as fact. Status is only ever "deficient" or
    "meets_or_exceeds", never "excess".
  - Does not solve or recommend changes to the ration -- see
    decision/solve_diet.py (not yet built) for that.
"""

from __future__ import annotations

from dataclasses import dataclass

from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget
from anllms.simulation.requirements_report import (
    RequirementsReport,
    build_requirements_report,
)

# If the ration's own total kg DM/d differs from the model's predicted
# DMI (the number actually driving every supply/balance figure) by more
# than this fraction, surface it as a first-class flag, not just a
# buried warning string.
DMI_MISMATCH_WARNING_THRESHOLD_PCT = 10.0


@dataclass
class NutrientEvaluation:
    name: str
    requirement: float
    supply: float | None
    unit: str
    balance: float | None
    pct_of_requirement: float | None
    status: str  # "deficient" | "meets_or_exceeds" | "not_available"


@dataclass
class DietEvaluation:
    report: RequirementsReport  # full underlying report, for drill-down/explain
    dmi_used_kg: float
    ration_total_dmi_kg: float
    dmi_mismatch_pct: float
    dmi_mismatch_flag: bool
    nel: NutrientEvaluation
    mp: NutrientEvaluation
    minerals: list[NutrientEvaluation]
    vitamins: list[NutrientEvaluation]
    deficient_nutrients: list[str]  # names only, for a quick "what's short" summary
    warnings: list[str]


def _evaluate(name: str, requirement: float, supply, unit: str, balance) -> NutrientEvaluation:
    if supply is None or balance is None:
        return NutrientEvaluation(name, requirement, supply, unit, balance, None, "not_available")
    pct = (supply / requirement * 100.0) if requirement else None
    status = "deficient" if balance < 0 else "meets_or_exceeds"
    return NutrientEvaluation(name, requirement, supply, unit, balance, pct, status)


def evaluate_diet(animal: AnimalState, milk: MilkTarget, ration: Ration) -> DietEvaluation:
    """
    Evaluate a REAL, already-specified ration against NASEM (2021)
    requirements. Raises ValueError if the ration is empty -- callers
    (chat tool included) must not substitute a placeholder diet here;
    that fallback belongs to the general/no-ration-given tool only.
    """
    if not ration.feedstuffs:
        raise ValueError(
            "evaluate_diet() requires a real ration with at least one "
            "ingredient. This function never falls back to a placeholder "
            "diet -- if the caller doesn't have a real ration yet, ask "
            "the user for one instead of calling this."
        )

    report = build_requirements_report(animal, milk, ration)

    ration_total = float(ration.total_dmi_kg)
    dmi_used = float(report.dmi_result.value)
    mismatch_pct = abs(ration_total - dmi_used) / dmi_used * 100.0 if dmi_used else 0.0
    mismatch_flag = bool(mismatch_pct > DMI_MISMATCH_WARNING_THRESHOLD_PCT)

    warnings = list(report.warnings)
    if mismatch_flag:
        warnings.insert(
            0,
            f"This ration totals {ration_total:.2f} kg DM/d, but the "
            f"model's predicted intake (used to drive every supply and "
            f"balance figure below) is {dmi_used:.2f} kg DM/d -- a "
            f"{mismatch_pct:.0f}% difference. Every balance number in "
            f"this evaluation reflects the PREDICTED intake, not the "
            f"ration's own total. If the client's cow is actually eating "
            f"close to {ration_total:.2f} kg DM/d rather than the "
            f"predicted value, these balances may not reflect real-world "
            f"intake.",
        )

    nel = _evaluate(
        "NEL", report.total_nel_requirement_mcal, report.nel_supply_total.value,
        "Mcal/d", report.nel_balance_mcal,
    )
    mp = _evaluate(
        "MP", report.total_mp_requirement_g, report.mp_supply_total.value,
        "g/d", report.mp_balance_g,
    )

    minerals = []
    for symbol, result in report.mineral_results.items():
        supply = report.mineral_supplies.get(symbol)
        balance = report.mineral_balances.get(symbol)
        minerals.append(_evaluate(
            symbol, result.value, supply.value if supply else None, result.unit, balance,
        ))

    vitamins = []
    for symbol, result in report.vitamin_results.items():
        supply = report.vitamin_supplies.get(symbol)
        balance = report.vitamin_balances.get(symbol)
        vitamins.append(_evaluate(
            symbol, result.value, supply.value if supply else None, result.unit, balance,
        ))

    deficient = [n.name for n in ([nel, mp] + minerals + vitamins) if n.status == "deficient"]

    return DietEvaluation(
        report=report,
        dmi_used_kg=dmi_used,
        ration_total_dmi_kg=ration_total,
        dmi_mismatch_pct=mismatch_pct,
        dmi_mismatch_flag=mismatch_flag,
        nel=nel,
        mp=mp,
        minerals=minerals,
        vitamins=vitamins,
        deficient_nutrients=deficient,
        warnings=warnings,
    )
