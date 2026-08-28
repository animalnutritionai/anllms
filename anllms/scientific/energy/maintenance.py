"""
Energy requirement for maintenance — adult dairy cattle.

Source: NASEM (2021) Nutrient Requirements of Dairy Cattle, 8th Rev. Ed.,
Chapter 3 "Energy", section "Maintenance Requirements", Equation 3-13.
https://www.ncbi.nlm.nih.gov/books/NBK600598/

    NELmaint (Mcal/d) = 0.10 x BW^0.75

This value replaced the long-standing 0.08 x BW^0.75 used from NRC (1978)
through NRC (2001). The committee's own worked example: for a ~650 kg
Holstein cow, this change adds about 2.5 Mcal NEL/d relative to the old
coefficient. That published example is used as the validation case in
tests/test_maintenance_energy.py.
"""

from __future__ import annotations

from anllms.knowledge.models import (
    AlternativeEquation,
    Citation,
    EquationResult,
    KnowledgeEquation,
    Variable,
)
from anllms.knowledge.publications import (
    NASEM_DAIRY_2021,
    NASEM_DAIRY_2021_SOFTWARE,
    NASEM_BEEF_2016,
    NRC_DAIRY_2001,
)


class NELMaintenanceNASEM2021(KnowledgeEquation):
    """NEL requirement for maintenance of adult dairy cattle (NASEM 2021, Eq. 3-13)."""

    name = "Net Energy for Lactation (NEL) requirement for maintenance"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="3",
        section="Energy Requirements > Maintenance Requirements",
        equation_number="Equation 3-13",
    )

    variables = [
        Variable(
            symbol="BW",
            name="Body weight",
            unit="kg",
            description="Live body weight of the adult cow.",
            valid_range=(300.0, 1100.0),  # practical adult dairy cow range; not a hard published bound
        ),
    ]

    formula_text = "NELmaint (Mcal/d) = 0.10 x BW^0.75"

    assumptions = [
        "0.10 Mcal/kg metabolic BW (BW^0.75) already includes a normal activity "
        "allowance for cows housed in confinement (drylot/free-stall); it is not "
        "a pure fasting-heat-production value.",
        "No adjustment is included for heat stress, cold stress, breed, or body "
        "condition score — the committee found data insufficient to support such "
        "adjustments in this edition.",
        "Coefficient derived primarily from Beltsville Energy Metabolism Unit "
        "data reanalyzed by Moraes et al. (2015), biased toward the most recent "
        "(1984-1995) decade of that dataset.",
        "CORRECTED (was previously stated incorrectly in this codebase): this "
        "same 0.10 x BW^0.75 coefficient also applies to heifers (An_Parity_rl "
        "used as the physiological-state switch in the reference software), not "
        "just post-calving cows. Confirmed against nasem_dairy "
        "calculate_An_NEmUse_NS(), which is back-derived from ME of 0.15 and "
        "Km_NE_ME = 0.66 (0.15 x 0.66 = 0.099 =~ 0.10). Do NOT reintroduce a "
        "heifer exclusion without a citation.",
    ]

    applicability = (
        "Heifers and adult dairy cattle (lactating or dry) in confinement housing "
        "under thermoneutral conditions, EXCEPT nursing or recently weaned calves, "
        "which use different coefficients against empty body weight rather than "
        "live BW: 0.0769 x BW_empty^0.75 while consuming a liquid/mixed diet, or "
        "0.097 x BW_empty^0.75 once weaned (both from the reference software; not "
        "yet mapped to a book equation number in this codebase — see "
        "known_discrepancies). Do not apply this equation to animals under "
        "significant heat/cold stress without an explicit, separately-cited "
        "environmental adjustment."
    )

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "The reference software's own docstring for calculate_An_NEmUse_NS "
        "flags an internal open question: the km values it uses for calves "
        "(0.0769 for nursing, 0.097 for weaned, sourced from Table 10-1) are "
        "noted by the package authors as possibly inconsistent with Equation "
        "20-272 elsewhere in the book. This platform has not yet independently "
        "resolved that discrepancy against the primary text and does not use "
        "either calf coefficient yet — flagged here rather than guessed at.",
        "Frame/reserve NEL growth (Frm_NELgain/Rsrv_NELgain, Eq. 3-20c) is a "
        "CONFIRMED, DELIBERATE deferral, not an oversight -- not yet "
        "independently cited by this codebase. Zero-impact for the default "
        "AnimalState (frame_gain_kg_per_day=0, reserve_gain_kg_per_day=0), "
        "which covers any mature, non-growing lactating cow. Building it "
        "would require independently mapping nasem_dairy's growth-"
        "partitioning chain in body_composition.py first. See "
        "docs/architecture.md's Known Open Items.",
    ]

    limitations = [
        "Published 95% confidence interval on the coefficient is approximately "
        "\u00b10.06 (i.e., 0.10 \u00b1 0.06 Mcal/kg BW^0.75) — substantial animal-to-animal "
        "variation exists (cows of similar size/production can vary ~7-10% in "
        "actual maintenance requirement).",
        "Does not account for heat stress, even though heat stress is known to "
        "alter maintenance energy metabolism, because NASEM (2021) judged the "
        "available data insufficient to quantify it reliably for dairy cattle.",
        "Does not adjust for body condition score, though the underlying chamber "
        "data did not systematically record BCS.",
    ]

    alternatives_considered = [
        AlternativeEquation(
            citation=Citation(publication=NRC_DAIRY_2001, chapter="3", equation_number="(unnumbered, maintenance)"),
            coefficient_or_summary="NELmaint = 0.080 x BW^0.75",
            reason_not_selected=(
                "Superseded. NASEM (2021) committee found this value, in use "
                "since NRC (1978), underestimated maintenance requirements of "
                "modern, more metabolically active dairy cows; multiple newer "
                "studies (Kirkland & Gordon 1999; Xue et al. 2011; Dong et al. "
                "2015; Morris & Kononoff 2021, among others) supported coefficients "
                "of 0.09-0.14."
            ),
        ),
        AlternativeEquation(
            citation=Citation(publication=NASEM_BEEF_2016, table_number="Table 19-1"),
            coefficient_or_summary="NELmaint = 0.095 x BW^0.75 (beef dairy-breed adjustment)",
            reason_not_selected=(
                "This is the Beef NASEM (2016) dairy-breed-adjusted value, close "
                "to but not identical to the dairy committee's own 0.10 figure; "
                "the Dairy NASEM (2021) committee chose its own value derived "
                "directly from dairy-cow chamber data rather than adopting the "
                "beef-model figure."
            ),
        ),
    ]

    notes = (
        "This equation only yields the NEL requirement for maintenance. Total "
        "daily NEL requirement for a lactating cow additionally requires "
        "lactation (Eq. 3-14a/b/c), gestation (Eq. 3-18), and body-reserve "
        "change (Eq. 3-19a/b/c) components, each a separate knowledge object."
    )

    def calculate(self, bw_kg: float, parity: int = 1) -> EquationResult:
        """
        Calculate NELmaint by calling the reference implementation directly
        (nasem_dairy.calculate_An_NEmUse_NS), rather than recomputing the
        formula ourselves.

        Why call it instead of reimplementing it (reversed from an earlier
        version of this file): this codebase is meant to eventually be
        shared back to the University of Guelph project as a collaborative
        contribution. Building our explanation layer as a wrapper AROUND
        their real, tested function — instead of a separate parallel
        reimplementation — keeps their math as the single source of truth
        and makes our addition mergeable rather than a competing fork of
        the logic itself.

        Parameters
        ----------
        bw_kg : float
            Body weight in kg (maps to An_BW).
        parity : int
            Parity as used by the reference function's An_Parity_rl switch;
            use parity=0 only for pre-weaning/weaned calves (a different,
            not-yet-mapped branch — see known_discrepancies). Default of 1
            selects the adult-cow/heifer branch this equation documents.
        """
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")

        import nasem_dairy as nd  # imported here, not at module load, so this
        # file can still be inspected/tested without nasem_dairy installed
        # for anything that doesn't call calculate().

        value = nd.calculate_An_NEmUse_NS(
            An_StatePhys="Lactating Cow" if parity > 0 else "Heifer",
            An_BW=bw_kg,
            An_BW_empty=bw_kg,  # unused on the parity>0 branch this equation covers
            An_Parity_rl=parity,
            Dt_DMIn_ClfLiq=0,
        )

        return EquationResult(
            value=value,
            unit="Mcal/d",
            inputs_used={"BW (kg)": bw_kg, "Parity": parity},
            equation=self,
        )
