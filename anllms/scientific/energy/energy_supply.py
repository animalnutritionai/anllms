"""
Total energy supply from the diet — DE, ME, and NEL.

SCOPE DECISION, same reasoning as TotalMPSupplyNASEM2021: digestible
energy supply (An_DEIn) is a sum of DE contributions from digested NDF,
starch, residual organic matter, true protein, NPN-CP, and fatty acids
-- each requiring its own per-ingredient digestibility chain. That's too
deep to wrap function-by-function at this stage, so this equation wraps
a full nasem_dairy model run and extracts the supply-side energy values,
the same way RUP-derived MP supply was handled.

Chain (citable, unlike the DE derivation above):
    An_MEIn (Mcal/d) = An_DEIn - An_GasEOut - Ur_DEout
        [ME = DE minus methane energy loss minus urinary energy loss --
         standard energy partitioning, NASEM 2021 Chapter 3]
    An_NEIn (Mcal/d) = An_MEIn * 0.66
        [Equation 3-12: ME-to-NEL conversion efficiency = 0.66, the SAME
         0.66 already cited in NELMaintenanceNASEM2021 and
         LactationNELRequirementNASEM2021 -- confirms consistency rather
         than introducing a second, different efficiency figure]

Book citation for the 0.66 efficiency: NASEM (2021) Chapter 3, Equation
3-12, derived from Moraes et al. (2015) reanalysis of Beltsville Energy
Metabolism Unit data (mean 0.66, 95% CI 0.64-0.69).
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget


class TotalEnergySupplyNASEM2021(KnowledgeEquation):
    """Total energy supply from the diet: DE -> ME -> NEL (NASEM 2021, Eq. 3-12 for the ME->NEL step)."""

    name = "Total energy supply from the diet (DE, ME, NEL)"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="3",
        section="Energy Requirements",
        equation_number="Equation 3-12 (ME-to-NEL conversion, 0.66); DE and ME "
                         "derivation is a chained sum without one display "
                         "equation number -- see this module's docstring "
                         "for the scope decision",
    )

    variables = [
        Variable(symbol="An_DEIn", name="Digestible energy supply", unit="Mcal/d"),
        Variable(symbol="An_GasEOut", name="Methane energy loss", unit="Mcal/d"),
        Variable(symbol="Ur_DEout", name="Urinary energy loss", unit="Mcal/d"),
    ]

    formula_text = (
        "An_MEIn = An_DEIn - An_GasEOut - Ur_DEout\n"
        "An_NEIn = An_MEIn * 0.66   [Equation 3-12]"
    )

    assumptions = [
        "ME-to-NEL efficiency of 0.66 is a whole-diet average (Moraes et al. "
        "2015 reanalysis of Beltsville data, 1974-1995), the SAME figure "
        "already used for maintenance and lactation NEL requirement "
        "elsewhere in this codebase -- supply and requirement sides use "
        "the same conversion efficiency, as the book intends.",
        "No correction for dietary fat concentration is applied to this "
        "efficiency, per the book's own statement -- high-fat diets may "
        "have a different true ME-to-NEL efficiency than 0.66.",
        "DE supply itself (An_DEIn) is taken from the reference model's "
        "full nutrient-digestion chain, not independently re-derived here.",
    ]

    applicability = "Any dairy cattle diet with a full nasem_dairy model run available."

    limitations = [
        "Because DE supply is not decomposed into individually-cited "
        "sub-equations, a discrepancy here cannot be traced to one "
        "specific formula the way maintenance or lactation NEL "
        "requirement can.",
        "The 0.66 efficiency has a stated 95% CI of 0.64-0.69 -- individual "
        "diets could reasonably fall anywhere in that range.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "An_DEIn (digestible energy supply) is not decomposed into "
        "individually-cited sub-equations here, the same scope gap noted "
        "for TotalMPSupplyNASEM2021's RUP chain. Tracked as future work.",
    ]

    def calculate(
        self,
        animal: AnimalState,
        milk: MilkTarget,
        ration: Ration,
        dmi_kg: float,
        model_output=None,
    ) -> EquationResult:
        """
        If model_output is provided (from a prior run_full_model() call
        for the same scenario), it is reused instead of running the full
        model again.
        """
        if model_output is None:
            from anllms.simulation.nasem_model_bridge import run_full_model

            model_output = run_full_model(animal, milk, ration, dmi_kg)

        an_dein = model_output.get_value("An_DEIn")
        an_mein = model_output.get_value("An_MEIn")
        an_nein = model_output.get_value("An_NEIn")

        return EquationResult(
            value=an_nein,
            unit="Mcal/d",
            inputs_used={
                "DE supply (Mcal/d, An_DEIn)": an_dein,
                "ME supply (Mcal/d, An_MEIn)": an_mein,
                "NEL supply (Mcal/d, An_NEIn = ME x 0.66)": an_nein,
            },
            equation=self,
        )
