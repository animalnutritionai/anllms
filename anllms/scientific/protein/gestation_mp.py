"""
Gestation MP requirement — NASEM (2021), Equations 20-238/20-239.

    Gest_MPuse_g (g/d) = GrUter_NPgain / Ky_MP_NP     [Eq. 20-239]
    Ky_MP_NP = 0.33 (when gravid uterine NP gain is positive)  [Eq. 20-238,
        set to match NRC (2001)'s value for this coefficient]

SCOPE DECISION, same reasoning as TotalMPSupplyNASEM2021's RUP chain:
GrUter_NPgain (gravid uterine net protein gain) is itself the output of
a ~15-function chain in the reference software's dedicated gestation
module (uterine weight, gravid uterine weight, their day-by-day gain
rates, fetal weight -- essentially a full conceptus-growth sub-model).
That chain was not found citable in the same section of the book as the
other requirement equations; it appears to belong to a separate,
dedicated growth/conceptus-development discussion this codebase has not
mapped yet (tracked as a known_discrepancy below, consistent with how
this project scoped out frame/reserve growth for the same reason).

This equation wraps a full model run and cites the SPECIFIC,
confirmed conversion formula (Eq. 20-238/20-239) precisely, rather than
either decomposing the entire conceptus-growth chain or leaving the
whole gestation MP requirement uncited.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class GestationMPRequirementNASEM2021(KnowledgeEquation):
    """MP requirement for gestation (NASEM 2021, Eq. 20-238/20-239)."""

    name = "Metabolizable protein (MP) requirement for gestation"

    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6",
        equation_number="Equation 20-238 (Ky_MP_NP = 0.33) and Equation 20-239 "
                         "(Gest_MPuse_g = GrUter_NPgain / Ky_MP_NP)",
    )

    variables = [
        Variable(symbol="GrUter_NPgain", name="Gravid uterine net protein gain", unit="g/d",
                  description="From the reference model's gestation sub-model -- "
                              "see this module's SCOPE DECISION note."),
    ]

    formula_text = "Gest_MPuse_g = GrUter_NPgain / 0.33"

    assumptions = [
        "Ky_MP_NP (MP-to-NP conversion efficiency for gestation) is fixed "
        "at 0.33 when gravid uterine NP gain is positive -- set to match "
        "the value used in NRC (2001), per the book's own statement, not "
        "independently re-derived by the 2021 committee.",
        "Uses a different, lower efficiency than milk protein synthesis "
        "(0.69) or scurf/fecal protein (also 0.69) -- gestation protein "
        "deposition is a genuinely less efficient process, not an "
        "approximation collapsed to match the other MP-to-NP conversions "
        "elsewhere in this codebase.",
    ]

    applicability = "Pregnant dairy cattle. Zero for non-pregnant cows (gestation_day=0)."

    limitations = [
        "The underlying gravid uterine NP gain curve is not independently "
        "decomposed in this codebase -- see known_discrepancies.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "GrUter_NPgain (and the broader gravid uterine/fetal growth chain "
        "it depends on) is not independently cited in this codebase -- it "
        "is read from the shared full-model run. This chain was not found "
        "in the same requirements-chapter book sections as the rest of "
        "this codebase's citations; it likely belongs to a separate "
        "conceptus-growth discussion not yet mapped, the same scope gap "
        "noted for frame/reserve body growth elsewhere in this project.",
    ]

    def calculate(self, model_output) -> EquationResult:
        """
        Takes a ModelOutput from a prior run_full_model() call (shared
        with the rest of a RequirementsReport) rather than running the
        model again.
        """
        value = model_output.Requirements["protein"]["Gest_MPUse_g_Trg"]

        return EquationResult(
            value=value,
            unit="g/d",
            inputs_used={
                "Gest_MPUse_g_Trg (g/d, from shared model run)": value,
                "Ky_MP_NP (efficiency)": 0.33,
            },
            equation=self,
        )
