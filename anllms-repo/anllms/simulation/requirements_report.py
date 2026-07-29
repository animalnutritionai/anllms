"""
Requirements Report — Simulation Layer.

This composes every knowledge object mapped so far AND cross-checks them
against the reference software's own official totals, rather than
treating our independently-summed components as authoritative on their
own. This matters because we discovered (see project history) that
building a second, independent computation path for the same number is a
real risk, not a hypothetical one -- the reference software already
computes official total MP and NEL requirements (Trg_MPIn_req,
Trg_NELuse) as part of a full model run, including components (gestation,
growth, body reserve) this codebase hasn't independently cited yet.

WHAT THIS DOES:
  1. Predicts DMI via our own cited equations (Eq. 2-1 or 2-2, diet-aware
     when the cow is >60 DIM) -- this stays ours since no equivalent
     "which DMI equation applies to this cow" selection logic exists
     ready-made in the reference software's public API.
  2. Runs the real reference model ONCE (via nasem_model_bridge) using
     that DMI, for the given AnimalState/MilkTarget/Ration.
  3. Takes OFFICIAL total MP and NEL requirements directly from that run
     (Trg_MPIn_req, Trg_NELuse) as the authoritative totals.
  4. ALSO computes our own cited component equations (MP maintenance, MP
     lactation, NEL maintenance, NEL lactation) purely for their
     individual citation/explanation value -- NOT as the source of the
     total.
  5. Reconciles the two: our component sum should equal the official
     total MINUS gestation/growth/reserve components we haven't
     individually cited yet (pulled from the same model run for
     transparency). Any gap beyond that is flagged as an unexplained
     discrepancy warning, not silently absorbed.
  6. Computes MP supply (microbial + RUP) from the SAME model run --
     TotalMPSupplyNASEM2021 accepts the already-run model_output so the
     full model is not run twice for one report.

WHAT THIS DELIBERATELY DOES NOT DO YET:
  - Does not independently cite gestation or growth/reserve MP/NEL
    equations -- their contribution is reported (from the reference
    model) for reconciliation purposes, but not individually explainable
    via our own KnowledgeEquation objects yet.
  - Does not optimize or recommend a diet. This is a reporting/explanation
    composition only.
  - Mineral/vitamin/water REQUIREMENTS use our own cited equations.
    Mineral/vitamin BALANCE (supply side) comes directly from the
    reference model's own output, NOT from independently-cited supply
    equations -- see simulation/mineral_vitamin_water.py's docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from anllms.knowledge.models import EquationResult
from anllms.feed_library.ration import Ration
from anllms.scientific.energy.dmi_lactating import DMIPredictionLactatingNASEM2021
from anllms.scientific.energy.dmi_lactating_diet_aware import (
    DMIPredictionLactatingDietAwareNASEM2021,
)
from anllms.scientific.energy.energy_supply import TotalEnergySupplyNASEM2021
from anllms.scientific.energy.lactation import LactationNELRequirementNASEM2021
from anllms.scientific.energy.maintenance import NELMaintenanceNASEM2021
from anllms.scientific.protein.milk_mp_requirement import MilkMPRequirementNASEM2021
from anllms.scientific.protein.mp_maintenance import MPMaintenanceRequirementNASEM2021
from anllms.scientific.protein.total_mp_supply import TotalMPSupplyNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget
from anllms.simulation.mineral_vitamin_water import (
    compute_mineral_balances,
    compute_mineral_results,
    compute_vitamin_balances,
    compute_vitamin_results,
    compute_water_result,
)
from anllms.simulation.nasem_model_bridge import run_full_model

RECONCILIATION_TOLERANCE = 0.5  # g (MP) or Mcal (NEL) -- small float-drift allowance


@dataclass
class RequirementsReport:
    """
    Bundles every component EquationResult plus the OFFICIAL totals from
    the reference model, so the AI Layer (or a human) can drill into any
    single cited component's full explanation while trusting the totals
    are the reference software's own, not a second independently-computed
    number.
    """

    dmi_result: EquationResult
    dmi_equation_used: str

    nel_maintenance: EquationResult
    nel_lactation: EquationResult
    total_nel_requirement_mcal: float          # OFFICIAL (Trg_NELuse), not our own sum
    nel_unexplained_gap_mcal: float             # official - (our components + gestation/growth/reserve)

    mp_maintenance: EquationResult
    mp_lactation: EquationResult
    total_mp_requirement_g: float               # OFFICIAL (Trg_MPIn_req), not our own sum
    mp_unexplained_gap_g: float

    mp_supply_total: EquationResult
    mp_balance_g: float

    nel_supply_total: EquationResult
    nel_balance_mcal: float

    mineral_results: dict[str, EquationResult]     # our cited requirement equations
    mineral_balances: dict[str, float]              # from the reference model directly

    vitamin_results: dict[str, EquationResult]      # our cited requirement equations
    vitamin_balances: dict[str, float]               # from the reference model directly

    water_result: EquationResult

    warnings: list[str]

    def summary(self) -> str:
        lines = [
            f"DMI prediction: {self.dmi_result.value:.2f} kg/d "
            f"(via {self.dmi_equation_used})",
            "",
            f"NEL requirement (official total): {self.total_nel_requirement_mcal:.2f} Mcal/d "
            f"[our cited maintenance {self.nel_maintenance.value:.2f} + "
            f"lactation {self.nel_lactation.value:.2f}; remainder is "
            f"gestation/growth/reserve, not yet individually cited]",
            f"NEL supply: {self.nel_supply_total.value:.2f} Mcal/d",
            f"NEL balance (supply - requirement): {self.nel_balance_mcal:.2f} Mcal/d",
            "",
            f"MP requirement (official total): {self.total_mp_requirement_g:.1f} g/d "
            f"[our cited maintenance {self.mp_maintenance.value:.1f} + "
            f"lactation {self.mp_lactation.value:.1f}; remainder is "
            f"gestation/growth/reserve, not yet individually cited]",
            "",
            f"MP supply (microbial + RUP): {self.mp_supply_total.value:.1f} g/d",
            f"MP balance (supply - requirement): {self.mp_balance_g:.1f} g/d",
            "",
            f"Water requirement (ad lib access assumed): {self.water_result.value:.1f} kg/d",
            "",
            "Minerals (requirement, balance -- balance from reference model, not independently cited):",
        ]
        for symbol, result in self.mineral_results.items():
            bal = self.mineral_balances.get(symbol)
            bal_str = f"{bal:.2f}" if bal is not None else "n/a"
            lines.append(f"  {symbol}: req {result.value:.2f} {result.unit}, balance {bal_str}")
        lines.append("")
        lines.append("Vitamins (requirement, balance -- balance from reference model, not independently cited):")
        for symbol, result in self.vitamin_results.items():
            bal = self.vitamin_balances.get(symbol)
            bal_str = f"{bal:.1f}" if bal is not None else "n/a"
            lines.append(f"  {symbol}: req {result.value:.1f} {result.unit}, balance {bal_str}")
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)


def build_requirements_report(
    animal: AnimalState, milk: MilkTarget, ration: Ration
) -> RequirementsReport:
    warnings: list[str] = []

    # --- Diet-level aggregates, derived from the real ration via their
    # own aggregation functions (see Ration.to_diet()), not manually entered ---
    diet = ration.to_diet()

    # --- DMI: use diet-aware equation only within its validated range
    # (>60 DIM, per the book restriction enforced in that equation itself) ---
    if animal.days_in_milk > 60:
        dmi_result = DMIPredictionLactatingDietAwareNASEM2021().calculate(
            diet_forage_ndf_pct=diet.forage_ndf_pct,
            diet_adf_pct=diet.adf_pct,
            diet_ndf_pct=diet.ndf_pct,
            forage_ndf_digestibility_pct=diet.forage_ndf_digestibility_pct,
            milk_yield_kg=milk.yield_kg,
            days_in_milk=animal.days_in_milk,
        )
        dmi_equation_used = "Eq. 2-2 (diet-aware; cow is >60 DIM)"
    else:
        prelim_nel_lactation = LactationNELRequirementNASEM2021().calculate(
            milk_yield_kg=milk.yield_kg,
            milk_fat_pct=milk.fat_pct,
            milk_true_protein_pct=milk.true_protein_pct,
            milk_lactose_pct=milk.lactose_pct,
        )
        dmi_result = DMIPredictionLactatingNASEM2021().calculate(
            bw_kg=animal.bw_kg,
            bcs=animal.bcs,
            lactation_day=animal.days_in_milk,
            parity=animal.parity,
            target_nel_milk_output=prelim_nel_lactation.value,
        )
        dmi_equation_used = "Eq. 2-1 (animal-only; cow is <=60 DIM, outside Eq. 2-2's validated range)"
        warnings.append(
            f"Cow is at {animal.days_in_milk} DIM (<=60), so the diet-aware DMI "
            f"equation (Eq. 2-2) could not be used per its own book-stated "
            f"restriction. DMI used here does not reflect this diet's "
            f"composition."
        )

    # --- Run the real reference model ONCE, shared by requirement totals
    # and MP supply below ---
    model_output = run_full_model(animal, milk, ration, dmi_result.value)

    # --- Energy: our cited components + official total + reconciliation ---
    nel_maintenance = NELMaintenanceNASEM2021().calculate(bw_kg=animal.bw_kg, parity=animal.parity)
    nel_lactation = LactationNELRequirementNASEM2021().calculate(
        milk_yield_kg=milk.yield_kg,
        milk_fat_pct=milk.fat_pct,
        milk_true_protein_pct=milk.true_protein_pct,
        milk_lactose_pct=milk.lactose_pct,
    )
    energy_req = model_output.Requirements["energy"]
    total_nel_official = energy_req["Trg_NELuse"]
    nel_gest_growth_reserve = (
        energy_req["Gest_NELuse"] + energy_req["Frm_NELgain"] + energy_req["Rsrv_NELgain"]
    )
    nel_unexplained_gap = total_nel_official - (
        nel_maintenance.value + nel_lactation.value + nel_gest_growth_reserve
    )
    if abs(nel_unexplained_gap) > RECONCILIATION_TOLERANCE:
        warnings.append(
            f"NEL requirement reconciliation gap of {nel_unexplained_gap:.2f} Mcal/d "
            f"is NOT fully explained by our cited components + the reference "
            f"model's gestation/growth/reserve terms. Investigate before trusting "
            f"this report for this scenario."
        )
    warnings.append(
        "NEL requirement components for gestation/growth/reserve are taken "
        "directly from the reference model's output, not from independently "
        "cited equations in this codebase yet -- see docs/architecture.md."
    )

    # --- Protein: our cited components + official total + reconciliation ---
    mp_maintenance = MPMaintenanceRequirementNASEM2021().calculate(
        bw_kg=animal.bw_kg, dmi_kg=dmi_result.value, diet_ndf_pct=diet.ndf_pct
    )
    mp_lactation = MilkMPRequirementNASEM2021().calculate(
        milk_yield_kg=milk.yield_kg, milk_true_protein_pct=milk.true_protein_pct
    )
    protein_req = model_output.Requirements["protein"]
    total_mp_official = protein_req["Trg_MPIn_req"]
    mp_gest_growth_reserve = (
        protein_req["Gest_MPUse_g_Trg"]
        + protein_req["Frm_MPUse_g_Trg"]
        + protein_req["Rsrv_MPUse_g_Trg"]
    )
    mp_unexplained_gap = total_mp_official - (
        mp_maintenance.value + mp_lactation.value + mp_gest_growth_reserve
    )
    if abs(mp_unexplained_gap) > RECONCILIATION_TOLERANCE:
        warnings.append(
            f"MP requirement reconciliation gap of {mp_unexplained_gap:.1f} g/d "
            f"is NOT fully explained by our cited components + the reference "
            f"model's gestation/growth/reserve terms. Investigate before trusting "
            f"this report for this scenario."
        )
    warnings.append(
        "MP requirement components for gestation/growth/reserve are taken "
        "directly from the reference model's output, not from independently "
        "cited equations in this codebase yet -- see docs/architecture.md."
    )

    # --- Protein supply: reuse the SAME model run, do not run the model twice ---
    mp_supply_total = TotalMPSupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=dmi_result.value,
        model_output=model_output,
    )

    mp_balance = mp_supply_total.value - total_mp_official

    # --- Energy supply: reuse the SAME model run, do not run the model twice ---
    nel_supply_total = TotalEnergySupplyNASEM2021().calculate(
        animal=animal, milk=milk, ration=ration, dmi_kg=dmi_result.value,
        model_output=model_output,
    )
    nel_balance = nel_supply_total.value - total_nel_official

    # --- Minerals: our cited requirement equations + official balances
    # from the same shared model run ---
    mineral_results = compute_mineral_results(animal, milk, dmi_kg=dmi_result.value)
    mineral_balances = compute_mineral_balances(model_output)
    warnings.append(
        "Mineral BALANCE values are taken directly from the reference "
        "model's output, not from independently cited supply equations -- "
        "see simulation/mineral_vitamin_water.py."
    )

    # --- Vitamins: our cited requirement equations + official balances ---
    vitamin_results = compute_vitamin_results(animal, milk)
    vitamin_balances = compute_vitamin_balances(model_output)
    warnings.append(
        "Vitamin BALANCE values are taken directly from the reference "
        "model's output, not from independently cited supply equations."
    )

    # --- Water: our cited requirement equation, diet inputs from the
    # shared model run (with the Dt_DM percent->fraction conversion) ---
    water_result = compute_water_result(dmi_kg=dmi_result.value, model_output=model_output)

    return RequirementsReport(
        dmi_result=dmi_result,
        dmi_equation_used=dmi_equation_used,
        nel_maintenance=nel_maintenance,
        nel_lactation=nel_lactation,
        total_nel_requirement_mcal=total_nel_official,
        nel_unexplained_gap_mcal=nel_unexplained_gap,
        mp_maintenance=mp_maintenance,
        mp_lactation=mp_lactation,
        total_mp_requirement_g=total_mp_official,
        mp_unexplained_gap_g=mp_unexplained_gap,
        mp_supply_total=mp_supply_total,
        mp_balance_g=mp_balance,
        nel_supply_total=nel_supply_total,
        nel_balance_mcal=nel_balance,
        mineral_results=mineral_results,
        mineral_balances=mineral_balances,
        vitamin_results=vitamin_results,
        vitamin_balances=vitamin_balances,
        water_result=water_result,
        warnings=warnings,
    )
