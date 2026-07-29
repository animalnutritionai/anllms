"""
Sulfur (S) requirement — NASEM (2021), Equation 20-439.

Simplest mineral requirement in the model: a single fixed proportion of
DMI, no maintenance/growth/gestation/lactation breakdown.

    An_S_req (g/d) = 2.0 * Dt_DMIn
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class SulfurRequirementNASEM2021(KnowledgeEquation):
    """Total sulfur requirement (NASEM 2021, Eq. 20-439)."""

    name = "Total sulfur (S) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-439")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "An_S_req (g/d) = 2.0 * Dt_DMIn"
    assumptions = [
        "No separate maintenance/growth/gestation/lactation breakdown -- "
        "unlike the macrominerals, S requirement is modeled as a single "
        "fixed proportion of DMI across all physiological states.",
    ]
    applicability = "Any dairy cattle with known DMI."
    limitations = ["Does not vary by production level, growth, or reproductive state."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_S_req(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)
