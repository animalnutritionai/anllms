"""
Vitamin A requirement — NASEM (2021), Equation 20-491.

    An_VitA_req (IU/d) = 110 * BW                         if MilkProd<=35
                        = 110*BW + 1000*(MilkProd-35)      if MilkProd>35

A flat maintenance-like baseline (110 IU/kg BW) with an extra allowance
kicking in only above 35 kg/d milk production.

NOTE on citation confidence: same extraction-gap pattern as iodine and
magnesium's gestation equation -- the display formula itself did not
extract as text, but its position (only equation between the "Vitamin A"
header and the balance equation, confirmed Eq. 20-492) makes Eq. 20-491
a confident attribution.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class VitaminARequirementNASEM2021(KnowledgeEquation):
    """Total vitamin A requirement (NASEM 2021, Eq. 20-491)."""

    name = "Total vitamin A requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="7/20",
        equation_number="Equation 20-491 (confident attribution by position; "
                         "formula text itself had a source-extraction gap)",
    )
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d"),
    ]
    formula_text = "An_VitA_req (IU/d) = 110*BW, or 110*BW + 1000*(MilkProd-35) if MilkProd>35"
    assumptions = [
        "Only the very highest producers (>35 kg/d) receive an additional "
        "vitamin A allowance above the flat BW-based baseline -- confirmed "
        "against real fixture data (20 and 35 kg/d give the identical "
        "66110 IU baseline; only 40 kg/d adds the extra 5000 IU).",
    ]
    applicability = "All non-calf dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float, milk_yield_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_VitA_req(Trg_MilkProd=milk_yield_kg, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="IU/d",
            inputs_used={"BW (kg)": bw_kg, "Milk yield (kg/d)": milk_yield_kg},
            equation=self,
        )
