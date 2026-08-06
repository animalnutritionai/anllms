"""
Gestation NEL requirement — NASEM (2021), Equations 20-236/20-237.

    Gest_MEuse (Mcal/d) = Gest_NEgain / Ky_ME_NE      [Eq. 20-237]
    Ky_ME_NE = 0.14 (when gravid uterine NE gain is positive)  [Eq. 20-236,
        derived from Ferrell et al. 1976]
    Gest_NELuse (Mcal/d) = Gest_MEuse * Kl_ME_NE   [Kl_ME_NE = 0.66, the
        same ME-to-NEL efficiency used throughout this codebase]

SCOPE DECISION: same as GestationMPRequirementNASEM2021 -- Gest_NEgain
(gravid uterine net energy gain) comes from the reference software's
dedicated gestation/conceptus-growth sub-model, not independently
decomposed here. See that module's docstring for the full reasoning.

HONEST NOTE ON THE REFERENCE SOFTWARE ITSELF: the function computing
Gest_NELuse carries the reference software's OWN inline comment
questioning it: "?? This should not be used, delete." This codebase
still uses it, since it IS the value the full model's own official
Trg_NELuse total is built from (confirmed by this codebase's own
reconciliation check elsewhere), but the maintainers' own uncertainty
about this specific line is recorded here rather than hidden.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class GestationNELRequirementNASEM2021(KnowledgeEquation):
    """NEL requirement for gestation (NASEM 2021, Eq. 20-236/20-237)."""

    name = "Net energy for lactation (NEL) requirement for gestation"

    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="3",
        equation_number="Equation 20-236 (Ky_ME_NE = 0.14, Ferrell et al. 1976) "
                         "and Equation 20-237 (Gest_MEuse = Gest_NEgain / Ky_ME_NE), "
                         "converted to NEL basis via Kl_ME_NE = 0.66",
    )

    variables = [
        Variable(symbol="Gest_NEgain", name="Gravid uterine net energy gain", unit="Mcal/d",
                  description="From the reference model's gestation sub-model -- "
                              "see this module's SCOPE DECISION note."),
    ]

    formula_text = "Gest_MEuse = Gest_NEgain / 0.14; Gest_NELuse = Gest_MEuse * 0.66"

    assumptions = [
        "Ky_ME_NE (ME-to-NE efficiency for gestation) is fixed at 0.14 "
        "when gravid uterine NE gain is positive -- a genuinely low "
        "efficiency compared to maintenance/lactation's 0.66, reflecting "
        "that energy deposition in fetal/uterine tissue is a costly "
        "process, not an error or simplification.",
        "The final Kl_ME_NE=0.66 conversion is the SAME ME-to-NEL "
        "efficiency already used for maintenance and lactation NEL "
        "requirement elsewhere in this codebase.",
    ]

    applicability = "Pregnant dairy cattle. Zero for non-pregnant cows (gestation_day=0)."

    limitations = [
        "The underlying gravid uterine NE gain curve is not independently "
        "decomposed in this codebase -- see known_discrepancies.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Gest_NEgain (and the broader gravid uterine/fetal growth chain "
        "it depends on) is not independently cited in this codebase -- "
        "read from the shared full-model run, same scope gap as "
        "GestationMPRequirementNASEM2021.",
        "The reference software's own source code carries an inline "
        "comment on this exact calculation questioning whether it "
        "should exist at all ('This should not be used, delete'). This "
        "codebase still uses it because it is the value the model's own "
        "official Trg_NELuse total is actually built from, but the "
        "maintainers' own uncertainty is recorded here rather than hidden.",
    ]

    def calculate(self, model_output) -> EquationResult:
        """
        Takes a ModelOutput from a prior run_full_model() call (shared
        with the rest of a RequirementsReport) rather than running the
        model again.
        """
        value = model_output.Requirements["energy"]["Gest_NELuse"]

        return EquationResult(
            value=value,
            unit="Mcal/d",
            inputs_used={
                "Gest_NELuse (Mcal/d, from shared model run)": value,
                "Ky_ME_NE (efficiency)": 0.14,
                "Kl_ME_NE (ME-to-NEL efficiency)": 0.66,
            },
            equation=self,
        )
