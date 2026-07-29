"""
Mineral, vitamin, and water composition helpers for RequirementsReport.

Kept in a separate module from requirements_report.py purely to avoid
that file becoming unmanageably long with 13 mineral + 3 vitamin calls --
no new science here, just orchestration calling the already-cited
equation objects in scientific/minerals/, scientific/vitamins/, and
scientific/water/.

BALANCE numbers (mineral/vitamin supply minus requirement) are pulled
from the shared reference-model run's own output, the same "full-model
supply" pattern already used for MP and NEL supply -- this codebase has
NOT built individually-cited mineral/vitamin SUPPLY equations (that would
mean wrapping per-ingredient absorption coefficients for 13 minerals + 3
vitamins, a large undertaking not yet done). REQUIREMENT numbers come
from our own cited equation objects; BALANCE numbers come from the
reference model directly and are labeled as such.
"""

from __future__ import annotations

from anllms.knowledge.models import EquationResult
from anllms.scientific.minerals.calcium import CalciumRequirementNASEM2021
from anllms.scientific.minerals.chlorine import ChlorineRequirementNASEM2021
from anllms.scientific.minerals.cobalt import CobaltRequirementNASEM2021
from anllms.scientific.minerals.copper import CopperRequirementNASEM2021
from anllms.scientific.minerals.iodine import IodineRequirementNASEM2021
from anllms.scientific.minerals.iron import IronRequirementNASEM2021
from anllms.scientific.minerals.magnesium import MagnesiumRequirementNASEM2021
from anllms.scientific.minerals.manganese import ManganeseRequirementNASEM2021
from anllms.scientific.minerals.phosphorus import PhosphorusRequirementNASEM2021
from anllms.scientific.minerals.potassium import PotassiumRequirementNASEM2021
from anllms.scientific.minerals.selenium import SeleniumRequirementNASEM2021
from anllms.scientific.minerals.sodium import SodiumRequirementNASEM2021
from anllms.scientific.minerals.sulfur import SulfurRequirementNASEM2021
from anllms.scientific.minerals.zinc import ZincRequirementNASEM2021
from anllms.scientific.vitamins.vitamin_a import VitaminARequirementNASEM2021
from anllms.scientific.vitamins.vitamin_d import VitaminDRequirementNASEM2021
from anllms.scientific.vitamins.vitamin_e import VitaminERequirementNASEM2021
from anllms.scientific.water.water_requirement import WaterRequirementLactatingNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget

# Maps our mineral symbol -> the reference model's own key in
# Requirements["mineral_requirements"], used to pull the official
# balance value from the shared model run.
_MINERAL_BALANCE_KEYS = {
    "Ca": "Ca", "P": "P", "Mg": "Mg", "Na": "Na", "Cl": "Cl", "K": "K",
    "S": "S", "Co": "Co", "Cu": "Cu", "Fe": "Fe", "Mn": "Mn", "Se": "Se",
    "Zn": "Zn", "I": "I",
}


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


def compute_mineral_balances(model_output) -> dict[str, float]:
    """
    Pull official mineral balance (supply - requirement) values from the
    shared reference-model run. NOT independently computed by this
    codebase -- see module docstring.
    """
    mineral_requirements = model_output.Requirements["mineral_requirements"]
    balances = {}
    for symbol, model_key in _MINERAL_BALANCE_KEYS.items():
        entry = mineral_requirements.get(model_key, {})
        bal_key = f"An_{model_key}_bal"
        if bal_key in entry:
            balances[symbol] = entry[bal_key]
    return balances


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


def compute_vitamin_balances(model_output) -> dict[str, float]:
    """Pull official vitamin balance values from the shared reference-model run."""
    vitamin_req = model_output.Requirements["vitamin"]
    return {
        "A": vitamin_req.get("An_VitA_bal"),
        "D": vitamin_req.get("An_VitD_bal"),
        "E": vitamin_req.get("An_VitE_bal"),
    }


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
