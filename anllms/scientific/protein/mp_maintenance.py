"""
Total metabolizable protein (MP) requirement for maintenance — NASEM (2021).

    An_MPm_g_Trg = Fe_MPendUse_g_Trg + Scrf_MPUse_g_Trg + Ur_MPendUse_g

Equivalent appendix formulation (Equations 20-304/20-305/20-306):
    An_NPmUse_g = Scrf_NP_g + Fe_NPend_g + Ur_NPend_g          [20-304]
    An_MPmUse_g = (An_NPmUse_g - Ur_NPend_g)/Km_MP_NP + Ur_NPend_g   [20-305]
    Km_MP_NP = 0.69                                             [20-306]

These two formulations are algebraically identical (the appendix version
factors urinary loss out before dividing by efficiency, then adds it back
undivided at 100% efficiency; the component-sum version divides scurf and
fecal by efficiency separately and adds urinary directly) — verified by
hand, not assumed. The reference software implements the component-sum
form; this codebase follows that for direct traceability to the mapped
functions.

The book explicitly deprecates the term "maintenance" for this sum,
preferring "nonproductive functions," because metabolic fecal protein (the
largest component) scales with DMI rather than reflecting true basal
metabolic cost — worth keeping in mind when explaining this number to a
user who may expect "maintenance" to mean something closer to fasting
requirements.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.scientific.protein.fecal_endogenous_mp import FecalEndogenousMPNASEM2021
from anllms.scientific.protein.scurf_mp import ScurfMPNASEM2021
from anllms.scientific.protein.urinary_endogenous_mp import UrinaryEndogenousMPNASEM2021


class MPMaintenanceRequirementNASEM2021(KnowledgeEquation):
    """Total MP requirement for maintenance (NASEM 2021, Eq. 20-304/20-305/20-306)."""

    name = "Metabolizable protein (MP) requirement for maintenance"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (derivation) / 20 (appendix, Eq. 20-304/20-305/20-306)",
        equation_number="Equation 20-304 (NP sum), Equation 20-305 (MP total), "
                         "Equation 20-306 (target efficiency)",
    )

    variables = [
        Variable(symbol="Fe_MPendUse_g_Trg", name="Fecal endogenous MP", unit="g/d",
                  description="From FecalEndogenousMPNASEM2021 (largest component)."),
        Variable(symbol="Scrf_MPUse_g_Trg", name="Scurf MP", unit="g/d",
                  description="From ScurfMPNASEM2021."),
        Variable(symbol="Ur_MPendUse_g", name="Urinary endogenous MP", unit="g/d",
                  description="From UrinaryEndogenousMPNASEM2021 (100% efficient, no division)."),
    ]

    formula_text = "An_MPm_g_Trg = Fe_MPendUse_g_Trg + Scrf_MPUse_g_Trg + Ur_MPendUse_g"

    assumptions = [
        "Composed from three independently-cited sub-equations, each with "
        "its own assumptions — see FecalEndogenousMPNASEM2021, "
        "ScurfMPNASEM2021, and UrinaryEndogenousMPNASEM2021 for details "
        "specific to each component.",
        "The book deliberately avoids calling this 'maintenance' internally "
        "(preferring 'nonproductive functions') because the dominant "
        "component (fecal endogenous loss) scales with DMI, not with a "
        "fasting/basal metabolic rate — this sum will increase substantially "
        "just from a cow eating more, independent of any true maintenance "
        "cost change.",
    ]

    applicability = "Adult (non-calf) dairy cattle, any physiological state (lactating, dry, gestating)."

    limitations = [
        "Inherits the unresolved book-internal coefficient discrepancies "
        "documented in FecalEndogenousMPNASEM2021 (11.62/0.134 vs 12.0/0.12) "
        "and ScurfMPNASEM2021 (0.85 vs 0.86) — this total is only as "
        "resolved as its least-resolved component.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Inherits both unresolved Chapter 6 vs Chapter 20 coefficient "
        "discrepancies from its fecal-endogenous and scurf components. Since "
        "fecal endogenous is the largest term, its discrepancy (~3% on that "
        "component) has the largest effect on this total.",
    ]

    notes = (
        "Total daily MP requirement = this (maintenance) + lactation "
        "(MilkMPRequirementNASEM2021) + gestation MP (not yet mapped) + body "
        "reserve MP (not yet mapped). Summed at the Simulation Layer, not "
        "inside any single equation, so each term stays independently "
        "inspectable and citable."
    )

    def calculate(self, bw_kg: float, dmi_kg: float, diet_ndf_pct: float) -> EquationResult:
        fecal_result = FecalEndogenousMPNASEM2021().calculate(
            dmi_kg=dmi_kg, diet_ndf_pct=diet_ndf_pct
        )
        scurf_result = ScurfMPNASEM2021().calculate(bw_kg=bw_kg)
        urinary_result = UrinaryEndogenousMPNASEM2021().calculate(bw_kg=bw_kg)

        import nasem_dairy as nd

        value = nd.calculate_An_MPm_g_Trg(
            Fe_MPendUse_g_Trg=fecal_result.value,
            Scrf_MPUse_g_Trg=scurf_result.value,
            Ur_MPendUse_g=urinary_result.value,
        )

        return EquationResult(
            value=value,
            unit="g/d",
            inputs_used={
                "BW (kg)": bw_kg,
                "DMI (kg/d)": dmi_kg,
                "Diet NDF (%)": diet_ndf_pct,
                "Fecal endogenous MP (g/d)": fecal_result.value,
                "Scurf MP (g/d)": scurf_result.value,
                "Urinary endogenous MP (g/d)": urinary_result.value,
            },
            equation=self,
        )
