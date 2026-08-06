"""
Dry matter intake (DMI) prediction — lactating dairy cows.
NASEM (2021) Equation 2-1 ("DMIn_eqn == 8" in the reference software).

    Dt_DMIn (kg/d) =
        (3.7 + 5.7*(Parity-1) + 0.305*Trg_NEmilkOut + 0.022*BW
         + (-0.689 - 1.87*(Parity-1)) * BCS)
        * (1 - (0.212 + 0.136*(Parity-1)) * exp(-0.053 * LactDay))

This is ONE of several DMI equations NASEM (2021)/the reference software
support (selected via DMIn_eqn 0-16 depending on animal class and data
availability). This module implements only the standard lactating-cow
equation (DMIn_eqn == 8), which does not depend on diet composition.

A second lactating-cow equation exists (Dt_DMIn_Lact2, DMIn_eqn == 9) that
DOES depend on diet NDF/ADF/forage composition — that one matters for diet
OPTIMIZATION specifically, since DMI then changes as the candidate diet
changes. It is intentionally NOT implemented yet; see known_discrepancies.
Do not assume Lact1's output is diet-composition-independent forever —
it's simply the equation this object currently wraps.
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


class DMIPredictionLactatingNASEM2021(KnowledgeEquation):
    """DMI prediction for lactating cows, standard form (NASEM 2021, Eq. 2-1)."""

    name = "Dry matter intake (DMI) prediction — lactating cows (standard equation)"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="2",
        section="Dry Matter Intake",
        equation_number="Equation 2-1 (reference software: DMIn_eqn == 8, "
                         "function calculate_Dt_DMIn_Lact1)",
    )

    variables = [
        Variable(symbol="BW", name="Body weight", unit="kg"),
        Variable(symbol="BCS", name="Body condition score", unit="1-5 scale",
                  description="NASEM uses a 1-5 BCS scale (not the 1-9 scale "
                              "used in some other systems)."),
        Variable(symbol="LactDay", name="Days in milk", unit="days"),
        Variable(symbol="Parity", name="Parity (number of calvings)", unit="count",
                  description="1 = first lactation (primiparous), 2+ = multiparous."),
        Variable(symbol="Trg_NEmilkOut", name="Target NEL output from milk", unit="Mcal/d",
                  description="From LactationNELRequirementNASEM2021 (Eq. 20-220)."),
    ]

    formula_text = (
        "DMI (kg/d) = (3.7 + 5.7*(Parity-1) + 0.305*Trg_NEmilkOut + 0.022*BW "
        "+ (-0.689 - 1.87*(Parity-1))*BCS) "
        "* (1 - (0.212 + 0.136*(Parity-1)) * exp(-0.053*LactDay))"
    )

    assumptions = [
        "Assumes a healthy cow with no significant disease, heat stress, or "
        "feed sorting/refusal behavior depressing intake below physiological "
        "capacity.",
        "BCS entered on the 1-5 scale used throughout NASEM (2021), not the "
        "1-9 scale used by some other scoring systems — using the wrong scale "
        "will silently produce a wrong DMI.",
        "Does not depend on diet composition (NDF, ADF, forage quality) — see "
        "known_discrepancies regarding the alternate Lact2 equation.",
    ]

    applicability = (
        "Lactating dairy cows only. Not applicable to dry cows, heifers, or "
        "calves, which each have their own dedicated DMI equations in the "
        "reference software (Dt_DMIn_DryCow1/2, Dt_DMIn_Heif_*, Dt_DMIn_Calf1)."
    )

    limitations = [
        "This is an empirical regression fit to a research population; "
        "individual-cow DMI can differ meaningfully from the prediction, "
        "especially outside the body weight/production ranges represented "
        "in the underlying dataset.",
        "Because it excludes diet composition, it will not reflect intake "
        "depression from high-NDF, low-quality forage diets — the diet-aware "
        "Lact2 equation would be needed for that.",
    ]

    alternatives_considered = [
        AlternativeEquation(
            citation=Citation(
                publication=NASEM_DAIRY_2021,
                equation_number="Equation 2-2 (appendix 20-22), function calculate_Dt_DMIn_Lact2",
            ),
            coefficient_or_summary=(
                "Diet-composition-dependent DMI equation using forage NDF, "
                "ADF:NDF ratio, 48h in vitro forage NDF digestibility, and "
                "milk yield instead of BW/BCS/lactation day/parity."
            ),
            reason_not_selected=(
                "Now implemented as DMIPredictionLactatingDietAwareNASEM2021 "
                "(scientific/energy/dmi_lactating_diet_aware.py). That equation "
                "is preferred for diet OPTIMIZATION and for cows >60 DIM, since "
                "it responds to the candidate diet's composition; this equation "
                "(Lact1) remains the right choice for cows <=60 DIM or "
                "non-Holstein cows, since Lact2 is explicitly restricted to "
                "Holstein cows past 60 DIM in the primary text."
            ),
        ),
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "The reference software's calculate_Dt_DMIn() dispatcher supports "
        "DMIn_eqn values 0 through roughly 16 covering calves, heifers "
        "(4 sub-variants), dry cows (2 phases), and both lactating-cow forms. "
        "Only the two lactating-cow forms (this equation and Lact2) are "
        "mapped here so far; dry cow, heifer, and calf DMI remain unmapped.",
    ]

    def calculate(
        self,
        bw_kg: float,
        bcs: float,
        lactation_day: int,
        parity: int,
        target_nel_milk_output: float,
    ) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if not (1.0 <= bcs <= 5.0):
            raise ValueError(
                f"bcs={bcs} is outside the NASEM 1-5 BCS scale; if this came "
                f"from a 1-9 scale source it must be converted first, not "
                f"passed through as-is."
            )
        if lactation_day < 0:
            raise ValueError("lactation_day cannot be negative")
        if parity < 1:
            raise ValueError("parity must be >= 1 (this equation is for lactating cows)")

        import nasem_dairy as nd

        value = nd.calculate_Dt_DMIn_Lact1(
            An_BW=bw_kg,
            An_BCS=bcs,
            An_LactDay=lactation_day,
            An_Parity_rl=parity,
            Trg_NEmilkOut=target_nel_milk_output,
        )

        return EquationResult(
            value=value,
            unit="kg/d",
            inputs_used={
                "BW (kg)": bw_kg,
                "BCS (1-5 scale)": bcs,
                "Days in milk": lactation_day,
                "Parity": parity,
                "Target NEL milk output (Mcal/d)": target_nel_milk_output,
            },
            equation=self,
        )
