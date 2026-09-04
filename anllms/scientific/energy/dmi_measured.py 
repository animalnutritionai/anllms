"""
Dry matter intake (DMI) — directly provided (measured/estimated), NOT
predicted. This is the "actual" half of the DMI actual-vs-predicted
dual-mode decision (see docs/architecture.md's Known Open Items,
resolved this session).

This is NOT an invented shortcut around NASEM's model. The reference
software itself supports exactly this mode: `nd.nasem()`'s
`DMIn_eqn == 0` setting means "use the caller-supplied `Trg_Dt_DMIn`
directly, skip DMI prediction entirely" — a real, named, official mode
of the reference software, not a workaround this codebase invented.
`simulation/nasem_model_bridge.py` has in fact always called
`nd.nasem()` with `DMIn_eqn: 0` and a `dmi_kg` value supplied by its
caller; previously that value only ever came from this codebase's own
Eq. 2-1/2-2 prediction. This equation object is what lets a caller
supply that same `dmi_kg` directly instead, with the same citation/
explain() machinery as every predicted-DMI path.

Expected primary use case (per project discussion, Aug 2026): a
nutrition specialist evaluating a real client cow will have an actual
measured or reliably estimated DMI in the large majority of cases and
should be able to use it directly, with the predictive equations
(DMIPredictionLactatingNASEM2021 / DMIPredictionLactatingDietAwareNASEM2021)
reserved as the fallback for when no real number is available.
"""

from __future__ import annotations

from anllms.knowledge.models import (
    Citation,
    EquationResult,
    KnowledgeEquation,
    Variable,
)
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class MeasuredDMINASEM2021(KnowledgeEquation):
    """DMI supplied directly by the caller (measured or reliably estimated),
    bypassing NASEM's predictive DMI equations entirely."""

    name = "Dry matter intake (DMI) — directly provided (measured/estimated), not predicted"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="2",
        section="Dry Matter Intake",
        equation_number=None,
        page_or_location=(
            "No numbered equation applies -- this is the reference "
            "software's DMIn_eqn == 0 mode (use Trg_Dt_DMIn directly), "
            "not a book formula."
        ),
    )

    variables = [
        Variable(
            symbol="Trg_Dt_DMIn",
            name="Directly provided (measured or estimated) dry matter intake",
            unit="kg/d",
            description=(
                "Supplied by the caller (e.g. a nutrition specialist's "
                "on-farm measured or estimated value for this specific "
                "cow), not derived from any NASEM prediction equation."
            ),
        ),
    ]

    formula_text = "DMI (kg/d) = Trg_Dt_DMIn (the value supplied directly by the caller)"

    assumptions = [
        "The caller has an accurate measured or reliably estimated DMI "
        "value for this specific cow and is deliberately choosing to "
        "bypass NASEM's predictive DMI equations (Eq. 2-1 / Eq. 2-2), "
        "the same choice the reference software's own DMIn_eqn == 0 "
        "setting represents.",
        "No plausibility check is applied to the supplied value here "
        "(e.g. against body weight or milk yield) -- if the entered "
        "number is wrong, every downstream requirement/supply/balance "
        "figure will reflect that error just as directly as a bad "
        "prediction-equation input would.",
    ]

    applicability = (
        "Any lactating-cow scenario where a real, trusted DMI value is "
        "already known. Preferred over the predictive equations "
        "whenever such a value is available, per project decision -- "
        "predicted DMI should be treated as the fallback for when no "
        "real number exists, not the default source of truth."
    )

    limitations = [
        "This equation object performs no calculation of its own -- it "
        "is a citation/explanation wrapper around a caller-supplied "
        "number, so its 'formula' is an identity, not a regression or "
        "physiological model. Its accuracy is entirely the accuracy of "
        "the caller's real-world measurement or estimate, not anything "
        "this codebase can verify.",
        "Unlike DMIPredictionLactatingDietAwareNASEM2021 (Eq. 2-2), a "
        "measured value does NOT automatically respond to a candidate "
        "diet's composition during optimization -- if a specialist "
        "supplies a measured DMI for the CURRENT diet and then asks the "
        "(not yet built) solver to explore materially different diets, "
        "that fixed DMI may no longer reflect what the cow would "
        "actually eat on a different ration. See docs/architecture.md "
        "for how solve_diet is expected to handle this.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "No book equation number applies to this path by design -- see "
        "citation.page_or_location above. This is not a citation gap; "
        "it is documented here so it is never mistaken for one.",
    ]

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")

        return EquationResult(
            value=dmi_kg,
            unit="kg/d",
            inputs_used={
                "Measured/estimated DMI (kg/d, supplied directly by caller)": dmi_kg,
            },
            equation=self,
        )
