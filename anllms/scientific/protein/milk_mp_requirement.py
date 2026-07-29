"""
Metabolizable protein (MP) requirement for milk production — target form.
NASEM (2021) Equations 20-213 and 20-214.

    Mlk_MPuse_Trg (kg/d) = Mlk_NP / Kl_MP_NP,Trg          [Eq. 20-213]
    Kl_MP_NP,Trg (g/g) = 0.69                              [Eq. 20-214]

IMPORTANT — there are TWO milk-MP concepts in NASEM (2021), and mixing them
up would silently produce wrong requirement numbers:

  1. Mlk_MPuse (Equation 20-212): uses a DYNAMIC efficiency computed from
     the actual diet/animal state (Equation 20-355). This describes how
     efficiently a GIVEN diet's MP supply is actually converted to milk
     protein under prevailing conditions. NOT implemented here.

  2. Mlk_MPuse_Trg (Equations 20-213/20-214, THIS equation): uses a FIXED
     target efficiency of 0.69, representing an achievable minimum/target
     efficiency from the literature. This is the REQUIREMENT-side number —
     "how much MP would a well-managed cow need to hit this milk protein
     target" — which is what diet formulation and this platform's
     requirement calculations need.

The book itself is explicit that the fixed 0.69 version is not a true
reflection of MP-to-milk-protein conversion under any specific diet; it is
a target/reference value. Do not present Mlk_MPuse_Trg output as "the"
efficiency of a given ration — it's a formulation target, not a prediction.
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
from anllms.scientific.protein.milk_net_protein import MilkNetProteinNASEM2021


class MilkMPRequirementNASEM2021(KnowledgeEquation):
    """MP requirement for milk production, target-efficiency form (NASEM 2021, Eq. 20-213/20-214)."""

    name = "Metabolizable protein (MP) requirement for milk production (target efficiency)"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="20 (appendix); underlying target value from Chapter 6",
        equation_number="Equation 20-213 (Mlk_MPuse_Trg) and Equation 20-214 "
                         "(Kl_MP_NP,Trg = 0.69)",
    )

    variables = [
        Variable(symbol="Mlk_NP", name="Net protein required for milk", unit="g/d",
                  description="From MilkNetProteinNASEM2021."),
        Variable(symbol="Kl_MP_NP,Trg", name="Target MP-to-NP conversion efficiency",
                  unit="g/g", description="Fixed at 0.69 per Equation 20-214."),
    ]

    formula_text = "Mlk_MPuse_Trg (g/d) = Mlk_NP (g/d) / 0.69"

    assumptions = [
        "Efficiency (0.69) is a FIXED TARGET value from Chapter 6, representing "
        "an achievable minimum efficiency observed in the literature — it is "
        "explicitly NOT a prediction of any specific diet's actual conversion "
        "efficiency (that would be the dynamic Eq. 20-212/20-355 pathway, not "
        "implemented here).",
        "The same 0.69 target is used elsewhere in NASEM (2021) for scurf and "
        "metabolic fecal protein efficiency (per Chapter 3's growth "
        "discussion), while endogenous urinary N is assumed 100% efficient "
        "(1.0) — these are related but distinct target efficiencies, not "
        "interchangeable.",
    ]

    applicability = (
        "Computing the MP REQUIREMENT to support a stated milk protein target "
        "in a well-managed cow — i.e., the formulation/requirement side of the "
        "equation, not a prediction of how efficiently a specific candidate "
        "diet will actually perform."
    )

    limitations = [
        "The book states explicitly that this fixed-efficiency prediction 'is "
        "not particularly accurate or precise' as a description of any real "
        "diet's performance — it is a target/reference, not a forecast.",
        "Does not vary with diet amino acid balance, energy adequacy, or "
        "other factors known to affect actual MP-to-milk-protein efficiency.",
    ]

    alternatives_considered = [
        AlternativeEquation(
            citation=Citation(publication=NASEM_DAIRY_2021, equation_number="Equation 20-212"),
            coefficient_or_summary="Mlk_MPuse using a dynamic efficiency from Equation 20-355",
            reason_not_selected=(
                "Reflects actual prevailing diet/animal conditions rather than "
                "a fixed target, so it answers a different question ('how "
                "efficient is THIS diet' vs 'what MP is REQUIRED'). Not yet "
                "implemented in this codebase — tracked as a future addition "
                "for diet EVALUATION (as opposed to requirement calculation)."
            ),
        ),
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    notes = (
        "Total daily MP requirement additionally requires maintenance "
        "(An_MPm_g_Trg — fecal endogenous + scurf + urinary endogenous, not "
        "yet mapped), gestation, and body reserve components, each its own "
        "knowledge object, summed at the Simulation Layer."
    )

    def calculate(self, milk_yield_kg: float, milk_true_protein_pct: float) -> EquationResult:
        np_result = MilkNetProteinNASEM2021().calculate(
            milk_yield_kg=milk_yield_kg, milk_true_protein_pct=milk_true_protein_pct
        )

        import nasem_dairy as nd

        value = nd.calculate_Mlk_MPUse_g_Trg(
            Trg_Mlk_NP_g=np_result.value,
            coeff_dict={"Kl_MP_NP_Trg": 0.69},
        )

        return EquationResult(
            value=value,
            unit="g/d",
            inputs_used={
                "Milk yield (kg/d)": milk_yield_kg,
                "Milk true protein (%)": milk_true_protein_pct,
                "Milk NP (g/d, from Trg_Mlk_NP_g)": np_result.value,
                "Target efficiency Kl_MP_NP,Trg": 0.69,
            },
            equation=self,
        )
