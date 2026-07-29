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
