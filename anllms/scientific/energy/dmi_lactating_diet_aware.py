"""
Dry matter intake (DMI) prediction — lactating cows, diet-composition-aware form.
NASEM (2021) Equation 2-2 (Chapter 2) / Equation 20-22 (appendix numbering).
Reference software: DMIn_eqn == 9, function calculate_Dt_DMIn_Lact2.

Source: Allen et al. (2019), fit on 134 treatment means from 34 experiments
(32 peer-reviewed papers, 1990-2015), Holstein cows only, 60-309 DIM.

    DMI (kg/d) = 12.0 - 0.107*fNDF + 8.17*(ADF/NDF) + 0.0253*fNDFD
                 - 0.328*(ADF/NDF - 0.602)*(fNDFD - 48.3)
                 + 0.225*MY + 0.00390*(fNDFD - 48.3)*(MY - 33.1)

Unlike Lact1 (Eq. 2-1), this equation responds to the ACTUAL diet being fed
(forage NDF, ADF:NDF ratio, forage NDF digestibility) rather than only
animal-side factors — which is exactly what a diet optimizer needs, since
predicted intake should change as candidate diets change.

IMPORTANT — verified directly against the primary text (not just the
reference software), the book states explicit restrictions the software's
bare function signature does not enforce:
  - Valid only for cows > 60 days in milk (DIM). Early lactation is
    explicitly excluded because the underlying data didn't include it and
    intake control is likely dominated by different (metabolic) mechanisms
    before 60 DIM.
  - Fit on HOLSTEIN cows only. Body weight was not a significant predictor
    and is not in the equation at all, so applicability to other breeds
    (Jerseys, crossbreds) is explicitly stated as unknown by the committee.
  - Data set had a single dominant forage per ration; multiple-forage diets
    need a DMI-weighted average fNDFD, per the book's own guidance.
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
from anllms.scientific.energy.dmi_lactating import DMIPredictionLactatingNASEM2021


class DMIPredictionLactatingDietAwareNASEM2021(KnowledgeEquation):
    """Diet-composition-aware DMI prediction for lactating cows >60 DIM (NASEM 2021, Eq. 2-2)."""

    name = "Dry matter intake (DMI) prediction — lactating cows, diet-composition-aware"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="2",
        section="Dry Matter Intake",
        equation_number="Equation 2-2 (appendix: Equation 20-22; reference software: "
                         "DMIn_eqn == 9, function calculate_Dt_DMIn_Lact2)",
    )

    variables = [
        Variable(symbol="Dt_fNDF", name="Forage NDF content of diet", unit="% of DM"),
        Variable(symbol="Dt_ADF", name="ADF content of diet", unit="% of DM"),
        Variable(symbol="Dt_NDF", name="NDF content of diet", unit="% of DM"),
        Variable(symbol="ForNDF48_NDF", name="Forage NDF digestibility (48h in vitro/in situ)",
                  unit="% of forage NDF",
                  description="Use a DMI-weighted average if diet has multiple forages; "
                              "use the dataset mean of 52.0% if unmeasured, per the book."),
        Variable(symbol="Milk_ProdTarget", name="Target/actual milk yield", unit="kg/d"),
    ]

    formula_text = (
        "DMI (kg/d) = 12.0 - 0.107*fNDF + 8.17*(ADF/NDF) + 0.0253*fNDFD "
        "- 0.328*(ADF/NDF - 0.602)*(fNDFD - 48.3) + 0.225*MY "
        "+ 0.00390*(fNDFD - 48.3)*(MY - 33.1)"
    )

    assumptions = [
        "Cow is past 60 days in milk (DIM) — explicitly stated in the book as "
        "the valid range; the underlying dataset (60-309 DIM) did not include "
        "early lactation.",
        "Cow is Holstein. Body weight was tested and found non-significant, so "
        "it is absent from the equation entirely; applicability to other "
        "breeds (Jersey, crossbreds) is explicitly stated as unknown.",
        "Ration contains a single dominant forage, or forage NDF digestibility "
        "(fNDFD) is a DMI-weighted average across multiple forages.",
        "Ration does not contain non-forage fiber sources (NFFS) in amounts "
        "large enough to shift ADF/NDF meaningfully beyond the dataset's range, "
        "and does not use ground/pelleted/very finely chopped material "
        "classified as 'forage.'",
    ]

    applicability = (
        "Lactating Holstein cows beyond 60 DIM, for diets with measured or "
        "reasonably estimated forage NDF, ADF, NDF, and forage NDF "
        "digestibility. This is the DMI equation appropriate for use INSIDE "
        "a diet optimizer, since it responds to the candidate diet's "
        "composition — Lact1 (Eq. 2-1) does not."
    )

    limitations = [
        "Fit on a research dataset (RMSE 1.55 kg/d, concordance correlation "
        "coefficient 0.83 in the original validation) — individual-farm "
        "accuracy will vary, especially outside the fNDF/ADF:NDF/fNDFD/MY "
        "ranges represented in that data.",
        "Explicitly not validated for cows <60 DIM; do not extrapolate "
        "backward into early lactation.",
        "No body-weight term at all, unlike Lact1 — cannot distinguish DMI "
        "capacity differences from cow size within this equation alone.",
    ]

    alternatives_considered = [
        AlternativeEquation(
            citation=Citation(publication=NASEM_DAIRY_2021, equation_number="Equation 2-1"),
            coefficient_or_summary="Animal-factor-only DMI (BW, BCS, DIM, parity, milk energy)",
            reason_not_selected=(
                "Ignores diet composition entirely, so it cannot respond to a "
                "candidate diet during optimization. Valid across all DIM "
                "(not restricted to >60 DIM) and not breed-restricted, so it "
                "remains the better choice for early lactation or non-Holstein "
                "cows — see DMIPredictionLactatingNASEM2021."
            ),
        ),
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "The reference software's function signature and docstring do not "
        "surface the >60 DIM or Holstein-only restrictions stated in the "
        "primary text — those were found only by checking the book directly "
        "(NASEM 2021, Chapter 2, near Equation 2-2). This equation object "
        "enforces the DIM restriction in calculate(); the reference software "
        "does not. If this equation is ever called through nasem_dairy "
        "directly elsewhere in the codebase without going through this "
        "wrapper, that enforcement will be silently skipped.",
    ]

    notes = (
        "For diet OPTIMIZATION specifically, prefer this equation over Lact1 "
        "when the cow is >60 DIM (per the book's own restriction), since "
        "intake should respond to the diet being evaluated. Fall back to "
        "DMIPredictionLactatingNASEM2021 (Eq. 2-1) for cows <=60 DIM or "
        "non-Holstein cows, where this equation is out of its validated range."
    )

    def calculate(
        self,
        diet_forage_ndf_pct: float,
        diet_adf_pct: float,
        diet_ndf_pct: float,
        forage_ndf_digestibility_pct: float,
        milk_yield_kg: float,
        days_in_milk: int,
    ) -> EquationResult:
        if days_in_milk <= 60:
            raise ValueError(
                f"days_in_milk={days_in_milk} is <=60; NASEM (2021) explicitly "
                f"states this equation is not valid before 60 DIM (see "
                f"Chapter 2 discussion of Equation 2-2). Use "
                f"DMIPredictionLactatingNASEM2021 (Eq. 2-1) instead for early "
                f"lactation."
            )
        if diet_ndf_pct <= 0:
            raise ValueError("diet_ndf_pct must be positive (used as a divisor)")

        import nasem_dairy as nd

        value = nd.calculate_Dt_DMIn_Lact2(
            Dt_ForNDF=diet_forage_ndf_pct,
            Dt_ADF=diet_adf_pct,
            Dt_NDF=diet_ndf_pct,
            Dt_ForDNDF48_ForNDF=forage_ndf_digestibility_pct,
            Trg_MilkProd=milk_yield_kg,
        )

        return EquationResult(
            value=value,
            unit="kg/d",
            inputs_used={
                "Diet forage NDF (%)": diet_forage_ndf_pct,
                "Diet ADF (%)": diet_adf_pct,
                "Diet NDF (%)": diet_ndf_pct,
                "Forage NDF digestibility (%)": forage_ndf_digestibility_pct,
                "Milk yield (kg/d)": milk_yield_kg,
                "Days in milk": days_in_milk,
            },
            equation=self,
        )
