"""
Requirements Report — Simulation Layer.

This composes every knowledge object mapped so far AND cross-checks them
against the reference software's own official totals, rather than
treating our independently-summed components as authoritative on their
own.

WHAT THIS DOES:
  1. Predicts DMI via our own cited equations (Eq. 2-1 or 2-2, diet-aware
     when the cow is >60 DIM).
  2. Runs the real reference model ONCE (via nasem_model_bridge), shared
     by every requirement, supply, and balance calculation below -- the
     full model is never run twice for one report.
  3. Takes OFFICIAL total MP and NEL requirements directly from that run
     (Trg_MPIn_req, Trg_NELuse) as the authoritative totals, while still
     computing our own cited component equations (maintenance, lactation)
     purely for their individual citation/explanation value, reconciled
     against the official total.
  4. Computes energy and MP supply via independently-cited equations
     (TotalEnergySupplyNASEM2021, TotalMPSupplyNASEM2021).
  5. Computes ALL 13 mineral and all 3 vitamin REQUIREMENTS via our own
     cited equations, and their SUPPLY via independently-cited supply
     equations (e.g. CalciumSupplyNASEM2021, Eq. 20-370/20-371) -- both
     sides of the balance are now independently cited, not just the
     requirement side. Balance = supply - requirement, composed by this
     codebase from two cited numbers, the same pattern as MP/NEL balance.
  6. Computes water requirement via our own cited equation (Eq. 9-1).

WHAT THIS DELIBERATELY DOES NOT DO YET:
  - Does not independently cite gestation or growth/reserve MP/NEL
    equations -- their contribution is reported (from the reference
    model) for reconciliation purposes, but not individually explainable
    via our own KnowledgeEquation objects yet.
  - Mineral/vitamin supply equations extract their value from the shared
    full-model run rather than independently re-summing per-ingredient
    contributions in this codebase -- see each supply equation's own
    known_discrepancies (same scope decision as RUP-derived MP supply
    and total energy supply elsewhere in this codebase).
  - Does not optimize or recommend a diet. This is a reporting/explanation
    composition only.
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
from anllms.scientific.energy.gestation_energy import GestationNELRequirementNASEM2021
from anllms.scientific.energy.lactation import LactationNELRequirementNASEM2021
from anllms.scientific.energy.maintenance import NELMaintenanceNASEM2021
from anllms.scientific.protein.gestation_mp import GestationMPRequirementNASEM2021
from anllms.scientific.protein.milk_mp_requirement import MilkMPRequirementNASEM2021
from anllms.scientific.protein.mp_maintenance import MPMaintenanceRequirementNASEM2021
from anllms.scientific.protein.total_mp_supply import TotalMPSupplyNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget
from anllms.simulation.mineral_vitamin_water import (
    compute_mineral_balances,
    compute_mineral_results,
    compute_mineral_supplies,
    compute_vitamin_balances,
    compute_vitamin_results,
    compute_vitamin_supplies,
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
    nel_gestation: EquationResult
    total_nel_requirement_mcal: float          # OFFICIAL (Trg_NELuse), not our own sum
    nel_unexplained_gap_mcal: float             # official - (our components, now including gestation)

    mp_maintenance: EquationResult
    mp_lactation: EquationResult
    mp_gestation: EquationResult
    total_mp_requirement_g: float               # OFFICIAL (Trg_MPIn_req), not our own sum
    mp_unexplained_gap_g: float

    mp_supply_total: EquationResult
    mp_balance_g: float

    nel_supply_total: EquationResult
    nel_balance_mcal: float

    mineral_results: dict[str, EquationResult]   # our cited requirement equations
    mineral_supplies: dict[str, EquationResult]  # our cited supply equations
    mineral_balances: dict[str, float]           # supply - requirement, composed by this codebase

    vitamin_results: dict[str, EquationResult]
    vitamin_supplies: dict[str, EquationResult]
    vitamin_balances: dict[str, float]

    water_result: EquationResult

    warnings: list[str]

    def summary(self) -> str:
        lines = [
            f"DMI prediction: {self.dmi_result.value:.2f} kg/d "
            f"(via {self.dmi_equation_used})",
            "",
            f"NEL requirement (official total): {self.total_nel_requirement_mcal:.2f} Mcal/d "
            f"[our cited maintenance {self.nel_maintenance.value:.2f} + "
            f"lactation {self.nel_lactation.value:.2f} + "
            f"gestation {self.nel_gestation.value:.2f}; remainder is "
            f"growth/reserve, not yet individually cited]",
            f"NEL supply: {self.nel_supply_total.value:.2f} Mcal/d",
            f"NEL balance (supply - requirement): {self.nel_balance_mcal:.2f} Mcal/d",
            "",
            f"MP requirement (official total): {self.total_mp_requirement_g:.1f} g/d "
            f"[our cited maintenance {self.mp_maintenance.value:.1f} + "
            f"lactation {self.mp_lactation.value:.1f} + "
            f"gestation {self.mp_gestation.value:.1f}; remainder is "
            f"growth/reserve, not yet individually cited]",
            "",
            f"MP supply (microbial + RUP): {self.mp_supply_total.value:.1f} g/d",
            f"MP balance (supply - requirement): {self.mp_balance_g:.1f} g/d",
            "",
            f"Water requirement (ad lib access assumed): {self.water_result.value:.1f} kg/d",
            "",
            "Minerals (requirement, supply, balance -- all independently cited):",
        ]
        for symbol, result in self.mineral_results.items():
            supply = self.mineral_supplies.get(symbol)
            bal = self.mineral_balances.get(symbol)
            supply_str = f"{supply.value:.2f}" if supply is not None else "n/a"
            bal_str = f"{bal:.2f}" if bal is not None else "n/a"
            lines.append(
                f"  {symbol}: req {result.value:.2f} {result.unit}, "
                f"supply {supply_str}, balance {bal_str}"
            )
        lines.append("")
        lines.append("Vitamins (requirement, supply, balance -- all independently cited):")
        for symbol, result in self.vitamin_results.items():
            supply = self.vitamin_supplies.get(symbol)
            bal = self.vitamin_balances.get(symbol)
            supply_str = f"{supply.value:.1f}" if supply is not None else "n/a"
            bal_str = f"{bal:.1f}" if bal is not None else "n/a"
            lines.append(
                f"  {symbol}: req {result.value:.1f} {result.unit}, "
                f"supply {supply_str}, balance {bal_str}"
            )
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

    # --- Run the real reference model ONCE, shared by everything below ---
    model_output = run_full_model(animal, milk, ration, dmi_result.value)

    # --- Energy: our cited components + official total + reconciliation ---
    nel_maintenance = NELMaintenanceNASEM2021().calculate(bw_kg=animal.bw_kg, parity=animal.parity)
    nel_lactation = LactationNELRequirementNASEM2021().calculate(
        milk_yield_kg=milk.yield_kg,
        milk_fat_pct=milk.fat_pct,
        milk_true_protein_pct=milk.true_protein_pct,
        milk_lactose_pct=milk.lactose_pct,
    )
    nel_gestation = GestationNELRequirementNASEM2021().calculate(model_output=model_output)
    energy_req = model_output.Requirements["energy"]
    total_nel_official = energy_req["Trg_NELuse"]
    nel_growth_reserve = energy_req["Frm_NELgain"] + energy_req["Rsrv_NELgain"]
    nel_unexplained_gap = total_nel_official - (
        nel_maintenance.value + nel_lactation.value + nel_gestation.value + nel_growth_reserve
    )
    if abs(nel_unexplained_gap) > RECONCILIATION_TOLERANCE:
        warnings.append(
            f"NEL requirement reconciliation gap of {nel_unexplained_gap:.2f} Mcal/d "
            f"is NOT fully explained by our cited components + the reference "
            f"model's growth/reserve terms. Investigate before trusting "
            f"this report for this scenario."
        )
    warnings.append(
        "NEL requirement growth/reserve components are taken directly "
        "from the reference model's output, not from independently "
        "cited equations in this codebase yet (gestation is now cited "
        "-- see docs/architecture.md for the remaining growth/reserve gap)."
    )

    # --- Protein: our cited components + official total + reconciliation ---
    mp_maintenance = MPMaintenanceRequirementNASEM2021().calculate(
        bw_kg=animal.bw_kg, dmi_kg=dmi_result.value, diet_ndf_pct=diet.ndf_pct
    )
    mp_lactation = MilkMPRequirementNASEM2021().calculate(
        milk_yield_kg=milk.yield_kg, milk_true_protein_pct=milk.true_protein_pct
    )
    mp_gestation = GestationMPRequirementNASEM2021().calculate(model_output=model_output)
    protein_req = model_output.Requirements["protein"]
    total_mp_official = protein_req["Trg_MPIn_req"]
    mp_growth_reserve = protein_req["Frm_MPUse_g_Trg"] + protein_req["Rsrv_MPUse_g_Trg"]
    mp_unexplained_gap = total_mp_official - (
        mp_maintenance.value + mp_lactation.value + mp_gestation.value + mp_growth_reserve
    )
    if abs(mp_unexplained_gap) > RECONCILIATION_TOLERANCE:
        warnings.append(
            f"MP requirement reconciliation gap of {mp_unexplained_gap:.1f} g/d "
            f"is NOT fully explained by our cited components + the reference "
            f"model's growth/reserve terms. Investigate before trusting "
            f"this report for this scenario."
        )
    warnings.append(
        "MP requirement growth/reserve components are taken directly "
        "from the reference model's output, not from independently "
        "cited equations in this codebase yet (gestation is now cited "
        "-- see docs/architecture.md for the remaining growth/reserve gap)."
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

    # --- Minerals: our cited requirement AND supply equations, balance
    # composed from both, same pattern as MP/NEL balance ---
    mineral_results = compute_mineral_results(animal, milk, dmi_kg=dmi_result.value)
    mineral_supplies = compute_mineral_supplies(model_output)
    mineral_balances = compute_mineral_balances(mineral_results, mineral_supplies)
    warnings.append(
        "Mineral supply equations extract their value from the shared "
        "full-model run rather than independently re-summing per-"
        "ingredient contributions in this codebase -- see each supply "
        "equation's known_discrepancies."
    )

    # --- Vitamins: our cited requirement AND supply equations ---
    vitamin_results = compute_vitamin_results(animal, milk)
    vitamin_supplies = compute_vitamin_supplies(model_output)
    vitamin_balances = compute_vitamin_balances(vitamin_results, vitamin_supplies)

    # --- Water: our cited requirement equation, diet inputs from the
    # shared model run ---
    water_result = compute_water_result(dmi_kg=dmi_result.value, model_output=model_output)

    return RequirementsReport(
        dmi_result=dmi_result,
        dmi_equation_used=dmi_equation_used,
        nel_maintenance=nel_maintenance,
        nel_lactation=nel_lactation,
        nel_gestation=nel_gestation,
        total_nel_requirement_mcal=total_nel_official,
        nel_unexplained_gap_mcal=nel_unexplained_gap,
        mp_maintenance=mp_maintenance,
        mp_lactation=mp_lactation,
        mp_gestation=mp_gestation,
        total_mp_requirement_g=total_mp_official,
        mp_unexplained_gap_g=mp_unexplained_gap,
        mp_supply_total=mp_supply_total,
        mp_balance_g=mp_balance,
        nel_supply_total=nel_supply_total,
        nel_balance_mcal=nel_balance,
        mineral_results=mineral_results,
        mineral_supplies=mineral_supplies,
        mineral_balances=mineral_balances,
        vitamin_results=vitamin_results,
        vitamin_supplies=vitamin_supplies,
        vitamin_balances=vitamin_balances,
        water_result=water_result,
        warnings=warnings,
    )
