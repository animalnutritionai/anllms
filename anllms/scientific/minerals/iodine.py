"""
Iodine (I) requirement — NASEM (2021), Equation 20-455.

Combines a metabolic-BW-scaled term with a linear milk-production term,
unlike the simple DMI-proportional form used for S/Co/Se:

    An_I_req (mg/d) = 0.216 * BW^0.528 + 0.1 * MilkProd   (adult, non-calf)

NOTE on citation confidence: the display formula for An_I_req itself did
not extract as text from the source document (the same narrow
extraction-gap pattern seen for magnesium's gestation equation), but its
position -- the only equation between the "Iodine" section header and the
balance equation (confirmed Eq. 20-456) -- makes Eq. 20-455 a confident
attribution.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class IodineRequirementNASEM2021(KnowledgeEquation):
    """Total iodine requirement (NASEM 2021, Eq. 20-455)."""

    name = "Total iodine (I) requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Equation 20-455 (confident attribution by position; "
                         "formula text itself had a source-extraction gap)",
    )
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d"),
    ]
    formula_text = "An_I_req (mg/d) = 0.216 * BW^0.528 + 0.1 * MilkProd (adult, non-calf)"
    assumptions = [
        "Combines a metabolic-BW term with a linear milk-production term, "
        "unlike the simple DMI-proportional form used for S/Co/Se.",
    ]
    applicability = "Adult (non-calf) dairy cattle. Calves use a different DMI-proportional formula (0.8*DMIn), not implemented here."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float, milk_yield_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_I_req(
            An_StatePhys="Lactating Cow", An_DMIn=0, An_BW=bw_kg, Trg_MilkProd=milk_yield_kg
        )
        return EquationResult(
            value=value, unit="mg/d",
            inputs_used={"BW (kg)": bw_kg, "Milk yield (kg/d)": milk_yield_kg},
            equation=self,
        )


class IodineSupplyNASEM2021(KnowledgeEquation):
    """Iodine supply from the diet (NASEM 2021, part of Eq. 20-456)."""

    name = "Iodine (I) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Dt_IIn, used directly in balance Equation 20-456")
    variables = [Variable(symbol="Dt_IIn", name="Dietary iodine intake", unit="mg/d")]
    formula_text = "Supply = Dt_IIn (no absorption coefficient applied)"
    assumptions = ["No absorption efficiency step -- raw dietary intake used directly as supply, same pattern as sulfur/selenium."]
    applicability = "Any lactating dairy cow diet."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Dt_IIn")
        return EquationResult(value=value, unit="mg/d", inputs_used={"Source": "Dt_IIn from shared model run"}, equation=self)
