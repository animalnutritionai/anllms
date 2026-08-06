"""
Cobalt (Co) requirement — NASEM (2021), Equation 20-442.

    An_Co_req (mg/d) = 0.2 * Dt_DMIn

Basis: dietary intake assuming no absorption/retention adjustment for a
calf (per the reference software's own comment on this function).
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class CobaltRequirementNASEM2021(KnowledgeEquation):
    """Total cobalt requirement (NASEM 2021, Eq. 20-442)."""

    name = "Total cobalt (Co) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-442")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "An_Co_req (mg/d) = 0.2 * Dt_DMIn"
    assumptions = [
        "Single fixed proportion of DMI across all physiological states -- "
        "cobalt is required by rumen microbes for vitamin B12 synthesis, "
        "so this requirement is a dietary intake target, not a "
        "physiological accretion estimate.",
    ]
    applicability = "Any dairy cattle with known DMI."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Co_req(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)


class CobaltSupplyNASEM2021(KnowledgeEquation):
    """Absorbed cobalt supply from the diet (NASEM 2021, Eq. 20-441)."""

    name = "Absorbed cobalt (Co) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-441")
    variables = [Variable(symbol="Fd_CoInf", name="Cobalt intake per ingredient", unit="mg/d")]
    formula_text = "Abs_CoIn = sum(Fd_absCoInf) across ration"
    assumptions = ["Per-ingredient absorption coefficient from the real feed library."]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_CoIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this codebase.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_CoIn")
        return EquationResult(value=value, unit="mg/d", inputs_used={"Source": "Abs_CoIn from shared model run"}, equation=self)
