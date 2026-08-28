"""
Total NEL requirement for lactation — NASEM (2021), appendix Equation 20-220.

    Trg_Mlk_NEout (Mcal/d) = Trg_MilkProd (kg/d) x Trg_NEmilk_Milk (Mcal/kg)

This is deliberately a thin equation — it just multiplies milk yield by the
per-kg energy content from NEmilkPerKgNASEM2021 (Eq. 3-14b/c). It is kept
as its own knowledge object (rather than folded into that one) because the
book and reference software both treat "how much energy is in a kg of milk"
and "how much milk is the cow making" as separately-sourced/citable pieces.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.scientific.energy.milk_composition import NEmilkPerKgNASEM2021


class LactationNELRequirementNASEM2021(KnowledgeEquation):
    """Total daily NEL requirement for milk production (NASEM 2021, Eq. 20-220)."""

    name = "Net Energy for Lactation (NEL) requirement for milk production"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="20 (appendix compilation); underlying logic from Chapter 3",
        equation_number="Equation 20-220",
    )

    variables = [
        Variable(symbol="Trg_MilkProd", name="Target milk production", unit="kg/d",
                  description="Target or actual milk yield."),
        Variable(symbol="Trg_NEmilk_Milk", name="Energy content of milk", unit="Mcal/kg",
                  description="From NEmilkPerKgNASEM2021 (Eq. 3-14b/c)."),
    ]

    formula_text = "Trg_Mlk_NEout (Mcal/d) = Trg_MilkProd (kg/d) x Trg_NEmilk_Milk (Mcal/kg)"

    assumptions = [
        "Milk energy content (Trg_NEmilk_Milk) must itself be citation-backed — "
        "this equation does not independently validate that value, it composes "
        "whatever NEmilkPerKgNASEM2021 (or an equivalent cited source) produced.",
        "Represents ENERGY REQUIREMENT for the stated production level, not "
        "energy actually captured; efficiency of converting diet energy into "
        "milk energy is handled by separate ME/NE conversion equations, not here.",
    ]

    applicability = (
        "Any lactating dairy cow with a defined target/actual milk production "
        "level and known or estimated milk composition."
    )

    limitations = [
        "Does not itself account for early-lactation energy mobilization from "
        "body reserves — that is handled by separate body-reserve equations "
        "(Eq. 3-19a/b/c) which combine with this value for total requirement.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Body reserve NEL change (Rsrv_NELgain, Eq. 3-19a/b/c, part of Eq. "
        "3-20c) -- a component of TOTAL NEL requirement, not this "
        "equation's own lactation term -- is a CONFIRMED, DELIBERATE "
        "deferral, not an oversight. Not yet independently cited by this "
        "codebase; zero-impact for the default AnimalState "
        "(reserve_gain_kg_per_day=0), which covers any mature, "
        "non-growing lactating cow. See energy/maintenance.py's "
        "known_discrepancies and docs/architecture.md's Known Open Items "
        "for the same deferral on the frame-growth side.",
    ]

    notes = (
        "Total daily NEL requirement for a lactating cow = this (lactation) + "
        "maintenance (NELMaintenanceNASEM2021) + gestation (Eq. 3-18) + body "
        "reserve change (Eq. 3-19a/b/c). Each remains its own knowledge object; "
        "summing them is a Simulation Layer concern, not done inside any one "
        "equation, so each term stays independently inspectable."
    )

    def calculate(
        self,
        milk_yield_kg: float,
        milk_fat_pct: float,
        milk_true_protein_pct: float | None = None,
        milk_lactose_pct: float | None = None,
    ) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")

        ne_per_kg_result = NEmilkPerKgNASEM2021().calculate(
            milk_fat_pct=milk_fat_pct,
            milk_true_protein_pct=milk_true_protein_pct,
            milk_lactose_pct=milk_lactose_pct,
        )

        import nasem_dairy as nd

        value = nd.calculate_Trg_Mlk_NEout(
            Trg_MilkProd=milk_yield_kg,
            Trg_NEmilk_Milk=ne_per_kg_result.value,
        )

        return EquationResult(
            value=value,
            unit="Mcal/d",
            inputs_used={
                "Milk yield (kg/d)": milk_yield_kg,
                "NEmilk (Mcal/kg, from Eq. 3-14b/c)": ne_per_kg_result.value,
            },
            equation=self,
        )
