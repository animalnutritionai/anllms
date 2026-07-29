"""
Selenium (Se) requirement — NASEM (2021), Equation 20-478.

    An_Se_req (mg/d) = 0.3 * Dt_DMIn
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class SeleniumRequirementNASEM2021(KnowledgeEquation):
    """Total selenium requirement (NASEM 2021, Eq. 20-478)."""

    name = "Total selenium (Se) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-478")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "An_Se_req (mg/d) = 0.3 * Dt_DMIn"
    assumptions = ["Single fixed proportion of DMI across all physiological states, same pattern as sulfur and cobalt."]
    applicability = "Any dairy cattle with known DMI."
    limitations = ["Selenium has a narrow safety margin between deficiency and toxicity; this requirement figure alone does not address maximum tolerable intake."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Se_req(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)
