"""
Net energy content of milk, per kg — NASEM (2021) Equation 3-14b / 3-14c.

Source: NASEM (2021) Nutrient Requirements of Dairy Cattle, 8th Rev. Ed.,
Chapter 3 "Energy". Also appears in the book's unified appendix numbering
as Equations 20-217 / 20-218.

Two published forms exist, selected by data availability:
  - 3-14b (fat, true protein, AND lactose % all known):
        NEmilk (Mcal/kg) = 9.29*Fat% /100 + 5.85*TP% /100 + 3.95*Lac% /100
  - 3-14c (only fat % known — fallback):
        NEmilk (Mcal/kg) = 0.36 + 9.69*Fat% /100      [Tyrrell & Reid, 1965]

Equation 3-14a (using crude protein instead of true protein) exists in the
book but is a documented gap: the reference software's own docstring notes
it is "not implemented." We inherit that same gap here rather than quietly
inventing a CP-based version — see known_discrepancies.
"""

from __future__ import annotations

from anllms.knowledge.models import (
    AlternativeEquation,
    Citation,
    EquationResult,
    KnowledgeEquation,
    Variable,
)
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class NEmilkPerKgNASEM2021(KnowledgeEquation):
    """Net energy content of milk per kg (NASEM 2021, Eq. 3-14b/3-14c)."""

    name = "Net energy content of milk (NEmilk), per kg"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="3",
        section="Energy Requirements > Lactation",
        equation_number="Equation 3-14b (full) / 3-14c (fat-only fallback); "
                         "also Equations 20-217/20-218 in the appendix numbering",
    )

    variables = [
        Variable(symbol="Fat%", name="Target milk fat percentage", unit="%",
                  description="Target/observed milk fat, e.g. 3.5 for 3.5%."),
        Variable(symbol="TP%", name="Target milk true protein percentage", unit="%",
                  description="True protein, not crude protein. Optional — triggers "
                              "fallback formula 3-14c if omitted."),
        Variable(symbol="Lac%", name="Target milk lactose percentage", unit="%",
                  description="Typically ~4.85%. Optional — triggers fallback "
                              "formula 3-14c if omitted."),
    ]

    formula_text = (
        "If TP% and Lac% known (3-14b): NEmilk = 9.29*Fat%/100 + 5.85*TP%/100 + 3.95*Lac%/100\n"
        "If only Fat% known (3-14c):    NEmilk = 0.36 + 9.69*Fat%/100"
    )

    assumptions = [
        "Fallback formula (3-14c) is not an independent NASEM (2021) derivation; "
        "it is the older Tyrrell & Reid (1965) fat-only regression, retained "
        "because lactose/true-protein data is often unavailable on-farm.",
        "Formula assumes 'typical' milk composition ranges; extreme values "
        "(e.g. very early lactation, mastitic milk) were not necessarily "
        "represented in the underlying composition data.",
    ]

    applicability = (
        "Lactating dairy cows with known or targeted milk fat percentage. Full "
        "3-14b form requires true protein and lactose percentages as well; "
        "falls back to 3-14c (fat-only) when either is unavailable."
    )

    limitations = [
        "3-14c is a fat-only approximation and will be less accurate than 3-14b "
        "whenever true protein or lactose differ substantially from typical values.",
    ]

    alternatives_considered = [
        AlternativeEquation(
            citation=Citation(publication=NASEM_DAIRY_2021, chapter="3", equation_number="Equation 3-14a"),
            coefficient_or_summary="NEmilk formula using crude protein (CP) instead of true protein (TP)",
            reason_not_selected=(
                "Present in the book but not implemented in the reference software "
                "(confirmed via its own docstring). We have not independently "
                "derived/verified this variant, so it is not offered here either — "
                "flagged as a known gap rather than guessed at."
            ),
        ),
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Equation 3-14a (crude-protein-based variant) is documented in the book "
        "but neither the reference software nor this codebase implements it. "
        "If a use case ever requires CP-based milk energy, this needs a fresh "
        "derivation from the primary text, not an assumption that it matches "
        "3-14b with CP substituted for TP.",
    ]

    notes = (
        "This equation produces energy PER KG of milk. It must be multiplied by "
        "milk yield (kg/d) to get the total lactation NEL requirement — see "
        "LactationNELRequirementNASEM2021 in scientific/energy/lactation.py."
    )

    def calculate(
        self,
        milk_fat_pct: float,
        milk_true_protein_pct: float | None = None,
        milk_lactose_pct: float | None = None,
    ) -> EquationResult:
        if milk_fat_pct < 0:
            raise ValueError("milk_fat_pct cannot be negative")

        import nasem_dairy as nd

        value = nd.calculate_Trg_NEmilk_Milk(
            Trg_MilkFatp=milk_fat_pct,
            Trg_MilkTPp=milk_true_protein_pct,
            Trg_MilkLacp=milk_lactose_pct,
        )

        return EquationResult(
            value=value,
            unit="Mcal/kg milk",
            inputs_used={
                "Milk fat (%)": milk_fat_pct,
                "Milk true protein (%)": milk_true_protein_pct,
                "Milk lactose (%)": milk_lactose_pct,
            },
            equation=self,
        )
