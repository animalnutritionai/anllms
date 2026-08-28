"""
Vitamin D requirement — NASEM (2021), Equation 20-493.

    An_VitD_req (IU/d) = 40 * BW   if lactating (MilkProd>0)
                        = 32 * BW   if not lactating

CONFIRMED directly from a paginated copy of the book (user-provided
screenshot, Aug 2026) -- the criteria table matches exactly. Previously
cited only by structural position (same extraction-gap pattern as
vitamin A -- see that module's docstring); that hedge is now resolved.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class VitaminDRequirementNASEM2021(KnowledgeEquation):
    """Total vitamin D requirement (NASEM 2021, Eq. 20-493)."""

    name = "Total vitamin D requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="7/20",
        equation_number="Equation 20-493 (confirmed by direct paginated read, Aug 2026)",
    )
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d", description="Used only to select lactating vs non-lactating coefficient."),
    ]
    formula_text = "An_VitD_req (IU/d) = 40*BW if lactating, else 32*BW"
    assumptions = [
        "Lactating cows have a ~25% higher vitamin D requirement per kg "
        "BW than dry cows, regardless of the actual milk yield amount -- "
        "a step change at zero production, not a graded response.",
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

        value = nd.calculate_An_VitD_req(Trg_MilkProd=milk_yield_kg, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="IU/d",
            inputs_used={"BW (kg)": bw_kg, "Milk yield (kg/d)": milk_yield_kg},
            equation=self,
        )


class VitaminDSupplyNASEM2021(KnowledgeEquation):
    """Vitamin D supply from the diet (NASEM 2021, part of Eq. 20-494)."""

    name = "Vitamin D supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="7/20", equation_number="Dt_VitDIn, used directly in balance Equation 20-494")
    variables = [Variable(symbol="Dt_VitDIn", name="Dietary vitamin D intake", unit="IU/d")]
    formula_text = "Supply = Dt_VitDIn = sum(Fd_VitDIn) across ration -- no absorption coefficient applied"
    assumptions = ["No modeled absorption efficiency for vitamin D -- raw summed dietary intake used directly as supply."]
    applicability = "Any lactating dairy cow diet."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Dt_VitDIn")
        return EquationResult(value=value, unit="IU/d", inputs_used={"Source": "Dt_VitDIn from shared model run"}, equation=self)
