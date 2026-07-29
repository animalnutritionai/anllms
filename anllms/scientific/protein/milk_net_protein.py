"""
Net protein (NP) required for milk production — NASEM (2021).

    Trg_Mlk_NP_g (g/d) = Trg_MilkProd (kg/d) * 1000 * Trg_MilkTPp (%) / 100

This is a straightforward unit conversion (milk yield x true protein
fraction), used in Chapter 6 (Protein and Amino Acid Requirements) as the
starting point for the milk MP requirement chain. Unlike most equations in
this codebase, a search of the primary text did NOT turn up a distinct
equation number for this specific conversion — it appears inline in the
requirements narrative rather than as a separately numbered display
equation. This is flagged honestly in known_discrepancies rather than
guessing a number.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class MilkNetProteinNASEM2021(KnowledgeEquation):
    """Net protein required for milk production (NASEM 2021, Chapter 6)."""

    name = "Net protein (NP) required for milk production"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6",
        section="Protein and Amino Acid Requirements",
        equation_number="Not separately numbered in the primary text (see "
                         "known_discrepancies); reference software function "
                         "calculate_Trg_Mlk_NP_g",
    )

    variables = [
        Variable(symbol="Trg_MilkProd", name="Target milk production", unit="kg/d"),
        Variable(symbol="Trg_MilkTPp", name="Target milk true protein percentage", unit="%"),
    ]

    formula_text = "Trg_Mlk_NP_g (g/d) = Trg_MilkProd (kg/d) * 1000 * Trg_MilkTPp (%) / 100"

    assumptions = [
        "Uses TRUE protein percentage, not crude protein — consistent with "
        "the true-protein basis used throughout the MP system, distinct from "
        "the milk-energy equation's optional crude-protein caveat.",
    ]

    applicability = "Any lactating cow with a defined target milk yield and true protein percentage."

    limitations = [
        "Purely a unit conversion of a specified target; does not itself "
        "predict what milk protein percentage a diet will achieve — that is "
        "a separate, much more complex prediction (Equation 6-6 / 20-208, "
        "not yet mapped in this codebase).",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "No distinct display-equation number was found for this specific "
        "MilkProd x TPp conversion in the primary text search performed for "
        "this codebase (searched Chapter 6 and the Chapter 20 appendix "
        "narrative around Equations 20-208 through 20-214). It may be an "
        "inline/unlabeled step rather than a separately numbered equation, "
        "or may have been missed. Treat the equation_number field above as "
        "unresolved, not as confirmed absent, until someone checks directly "
        "against a paginated copy of the book.",
    ]

    def calculate(self, milk_yield_kg: float, milk_true_protein_pct: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        if milk_true_protein_pct < 0:
            raise ValueError("milk_true_protein_pct cannot be negative")

        import nasem_dairy as nd

        value = nd.calculate_Trg_Mlk_NP_g(
            Trg_MilkProd=milk_yield_kg,
            Trg_MilkTPp=milk_true_protein_pct,
        )

        return EquationResult(
            value=value,
            unit="g/d",
            inputs_used={
                "Milk yield (kg/d)": milk_yield_kg,
                "Milk true protein (%)": milk_true_protein_pct,
            },
            equation=self,
        )
