"""
Mineral, vitamin, and water composition helpers for RequirementsReport.

Kept in a separate module from requirements_report.py purely to avoid
that file becoming unmanageably long with 13 mineral + 3 vitamin calls --
no new science here, just orchestration calling the already-cited
equation objects in scientific/minerals/, scientific/vitamins/, and
scientific/water/.

UPDATED: mineral/vitamin SUPPLY is now computed via independently-cited
equation objects (CalciumSupplyNASEM2021, etc.), each with its own real
book citation (Eq. 20-370/20-371 for calcium, and so on through all 13
minerals + 3 vitamins). BALANCE (supply - requirement) is now composed
by THIS codebase from two independently-cited numbers, the same pattern
already used for MP and NEL balance -- not pulled as a single pre-labeled
field from the reference model. This closes the citation gap that
existed in the earlier version of this file.

Each supply equation still extracts its underlying value (Abs_CaIn, etc.)
from the shared full-model run rather than independently re-summing
per-ingredient contributions -- that remaining gap is documented in each
equation's own known_discrepancies, consistent with how RUP-derived MP
supply and total energy supply are handled elsewhere in this codebase.
"""

from __future__ import annotations

from anllms.knowledge.models import EquationResult
from anllms.scientific.minerals.calcium import CalciumRequirementNASEM2021, CalciumSupplyNASEM2021
from anllms.scientific.minerals.chlorine import ChlorineRequirementNASEM2021, ChlorineSupplyNASEM2021
from anllms.scientific.minerals.cobalt import CobaltRequirementNASEM2021, CobaltSupplyNASEM2021
from anllms.scientific.minerals.copper import CopperRequirementNASEM2021, CopperSupplyNASEM2021
from anllms.scientific.minerals.iodine import IodineRequirementNASEM2021, IodineSupplyNASEM2021
from anllms.scientific.minerals.iron import IronRequirementNASEM2021, IronSupplyNASEM2021
from anllms.scientific.minerals.magnesium import MagnesiumRequirementNASEM2021, MagnesiumSupplyNASEM2021
from anllms.scientific.minerals.manganese import ManganeseRequirementNASEM2021, ManganeseSupplyNASEM2021
from anllms.scientific.minerals.phosphorus import PhosphorusRequirementNASEM2021, PhosphorusSupplyNASEM2021
from anllms.scientific.minerals.potassium import PotassiumRequirementNASEM2021, PotassiumSupplyNASEM2021
from anllms.scientific.minerals.selenium import SeleniumRequirementNASEM2021, SeleniumSupplyNASEM2021
from anllms.scientific.minerals.sodium import SodiumRequirementNASEM2021, SodiumSupplyNASEM2021
from anllms.scientific.minerals.sulfur import SulfurRequirementNASEM2021, SulfurSupplyNASEM2021
from anllms.scientific.minerals.zinc import ZincRequirementNASEM2021, ZincSupplyNASEM2021
from anllms.scientific.vitamins.vitamin_a import VitaminARequirementNASEM2021, VitaminASupplyNASEM2021
from anllms.scientific.vitamins.vitamin_d import VitaminDRequirementNASEM2021, VitaminDSupplyNASEM2021
from anllms.scientific.vitamins.vitamin_e import VitaminERequirementNASEM2021, VitaminESupplyNASEM2021
from anllms.scientific.water.water_requirement import WaterRequirementLactatingNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget


def compute_mineral_results(animal: AnimalState, milk: MilkTarget, dmi_kg: float) -> dict[str, EquationResult]:
    """Compute all 13 mineral requirements using our own cited equation objects."""
    bw_mature = animal.bw_mature_kg or animal.bw_kg
    body_gain = animal.frame_gain_kg_per_day
    gest_day = animal.gestation_day

    return {
        "Ca": CalciumRequirementNASEM2021().calculate(
            dmi_kg=dmi_kg, bw_mature_kg=bw_mature, bw_kg=animal.bw_kg,
            body_gain_kg_per_day=body_gain, gestation_day=gest_day,
            milk_yield_kg=milk.yield_kg, milk_true_protein_pct=milk.true_protein_pct,
        ),
        "P": PhosphorusRequirementNASEM2021().calculate(
            bw_kg=animal.bw_kg, dmi_kg=dmi_kg, parity=animal.parity,
            bw_mature_kg=bw_mature, body_gain_kg_per_day=body_gain,
            gestation_day=gest_day, milk_yield_kg=milk.yield_kg,
            milk_true_protein_pct=milk.true_protein_pct,
        ),
        "Mg": MagnesiumRequirementNASEM2021().calculate(
            bw_kg=animal.bw_kg, dmi_kg=dmi_kg, body_gain_kg_per_day=body_gain,
            gestation_day=gest_day, milk_yield_kg=milk.yield_kg,
        ),
        "Na": SodiumRequirementNASEM2021().calculate(
            dmi_kg=dmi_kg, body_gain_kg_per_day=body_gain, gestation_day=gest_day,
            bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg,
        ),
        "Cl": ChlorineRequirementNASEM2021().calculate(
            dmi_kg=dmi_kg, body_gain_kg_per_day=body_gain, gestation_day=gest_day,
            bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg,
        ),
        "K": PotassiumRequirementNASEM2021().calculate(
            milk_yield_kg=milk.yield_kg, bw_kg=animal.bw_kg, dmi_kg=dmi_kg,
            body_gain_kg_per_day=body_gain, gestation_day=gest_day,
        ),
        "S": SulfurRequirementNASEM2021().calculate(dmi_kg=dmi_kg),
        "Co": CobaltRequirementNASEM2021().calculate(dmi_kg=dmi_kg),
        "Cu": CopperRequirementNASEM2021().calculate(
            bw_kg=animal.bw_kg, body_gain_kg_per_day=body_gain,
            gestation_day=gest_day, milk_yield_kg=milk.yield_kg,
        ),
        "Fe": IronRequirementNASEM2021().calculate(
            body_gain_kg_per_day=body_gain, gestation_day=gest_day,
            bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg,
        ),
        "Mn": ManganeseRequirementNASEM2021().calculate(
            bw_kg=animal.bw_kg, body_gain_kg_per_day=body_gain,
            gestation_day=gest_day, milk_yield_kg=milk.yield_kg,
        ),
        "Se": SeleniumRequirementNASEM2021().calculate(dmi_kg=dmi_kg),
        "Zn": ZincRequirementNASEM2021().calculate(
            dmi_kg=dmi_kg, body_gain_kg_per_day=body_gain, gestation_day=gest_day,
            bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg,
        ),
        "I": IodineRequirementNASEM2021().calculate(bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg),
    }


def compute_mineral_supplies(model_output) -> dict[str, EquationResult]:
    """Compute all 13 mineral supplies using our own cited equation objects."""
    return {
        "Ca": CalciumSupplyNASEM2021().calculate(model_output=model_output),
        "P": PhosphorusSupplyNASEM2021().calculate(model_output=model_output),
        "Mg": MagnesiumSupplyNASEM2021().calculate(model_output=model_output),
        "Na": SodiumSupplyNASEM2021().calculate(model_output=model_output),
        "Cl": ChlorineSupplyNASEM2021().calculate(model_output=model_output),
        "K": PotassiumSupplyNASEM2021().calculate(model_output=model_output),
        "S": SulfurSupplyNASEM2021().calculate(model_output=model_output),
        "Co": CobaltSupplyNASEM2021().calculate(model_output=model_output),
        "Cu": CopperSupplyNASEM2021().calculate(model_output=model_output),
        "Fe": IronSupplyNASEM2021().calculate(model_output=model_output),
        "Mn": ManganeseSupplyNASEM2021().calculate(model_output=model_output),
        "Se": SeleniumSupplyNASEM2021().calculate(model_output=model_output),
        "Zn": ZincSupplyNASEM2021().calculate(model_output=model_output),
        "I": IodineSupplyNASEM2021().calculate(model_output=model_output),
    }


def compute_mineral_balances(
    requirements: dict[str, EquationResult], supplies: dict[str, EquationResult]
) -> dict[str, float]:
    """
    Balance = supply - requirement, composed from two independently-cited
    numbers by THIS codebase -- no longer pulled as a single pre-labeled
    field from the reference model.
    """
    return {symbol: supplies[symbol].value - req.value for symbol, req in requirements.items()}


def compute_vitamin_results(animal: AnimalState, milk: MilkTarget) -> dict[str, EquationResult]:
    """Compute vitamin A, D, E requirements using our own cited equation objects."""
    return {
        "A": VitaminARequirementNASEM2021().calculate(bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg),
        "D": VitaminDRequirementNASEM2021().calculate(bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg),
        "E": VitaminERequirementNASEM2021().calculate(
            bw_kg=animal.bw_kg, milk_yield_kg=milk.yield_kg, parity=animal.parity,
            gestation_day=animal.gestation_day, is_pregnant=(animal.gestation_day > 0),
            pasture_dmi_kg=0.0,
        ),
    }


def compute_vitamin_supplies(model_output) -> dict[str, EquationResult]:
    """Compute vitamin A, D, E supplies using our own cited equation objects."""
    return {
        "A": VitaminASupplyNASEM2021().calculate(model_output=model_output),
        "D": VitaminDSupplyNASEM2021().calculate(model_output=model_output),
        "E": VitaminESupplyNASEM2021().calculate(model_output=model_output),
    }


def compute_vitamin_balances(
    requirements: dict[str, EquationResult], supplies: dict[str, EquationResult]
) -> dict[str, float]:
    """Balance = supply - requirement, composed by this codebase (see compute_mineral_balances)."""
    return {symbol: supplies[symbol].value - req.value for symbol, req in requirements.items()}


def compute_water_result(dmi_kg: float, model_output) -> EquationResult:
    """
    Compute water requirement using our own cited equation, pulling diet
    composition inputs (Na%, K%, CP%, DM%) from the shared model run.

    Dt_DM from the reference model's output is a PERCENTAGE (e.g. 64.9),
    matching every other diet composition field (Dt_NDF, Dt_ADF, etc.) --
    confirmed against a real full-model run (see
    scientific/water/water_requirement.py's module docstring CORRECTION
    note for the earlier incorrect fraction assumption this fixes).
    Passed straight through, no unit conversion needed.
    """
    diet_dm_pct = model_output.get_value("Dt_DM")
    diet_na_pct = model_output.get_value("Dt_Na")
    diet_k_pct = model_output.get_value("Dt_K")
    diet_cp_pct = model_output.get_value("Dt_CP")
    ambient_temp_c = model_output.get_value("Env_TempCurr")

    return WaterRequirementLactatingNASEM2021().calculate(
        dmi_kg=dmi_kg,
        diet_dm_pct=diet_dm_pct,
        diet_na_pct=diet_na_pct,
        diet_k_pct=diet_k_pct,
        diet_cp_pct=diet_cp_pct,
        ambient_temp_c=ambient_temp_c,
    )
