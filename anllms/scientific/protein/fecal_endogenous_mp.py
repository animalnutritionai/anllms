"""
Fecal endogenous (metabolic fecal protein, MFP) MP requirement — NASEM (2021).

    Fe_CPend_g (g/d) = (12.0 + 0.12*NDF%DM) * DMI      [Eq. 20-300, appendix]
    Fe_NPend_g (g/d) = Fe_CPend_g * 0.73                [Eq. 20-302]
    Fe_MPendUse_g_Trg = Fe_NPend_g / 0.69

CONFIRMED BOOK-INTERNAL DISCREPANCY: Chapter 6 (Equation 6-9a) states
CP-MFP = (11.62 + 0.134*NDF%DM) * DMI, while Chapter 20's appendix
(Equation 20-300) rounds/restates this as (12.0 + 0.12*NDF%DM) * DMI. The
reference software implements the Chapter 20 (rounded) coefficients
exactly. This is the same pattern as the scurf discrepancy: a Chapter 6
narrative equation and its Chapter 20 appendix restatement don't match
exactly, and the software follows the appendix. Flagged, not silently
resolved — see known_discrepancies. This is the LARGEST of the maintenance
MP components (the book itself calls metabolic fecal protein "the largest
contribution to so-called maintenance"), so the ~3% coefficient difference
between the two book versions is worth being aware of, not dismissing as
negligible.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class FecalEndogenousMPNASEM2021(KnowledgeEquation):
    """Fecal endogenous (metabolic fecal protein) MP requirement (NASEM 2021, Eq. 20-300/20-302)."""

    name = "Fecal endogenous (metabolic fecal protein) MP requirement"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (derivation, Eq. 6-9a) / 20 (appendix, Eq. 20-300/20-302/20-306)",
        equation_number="Equation 20-300 (Fe_CPend), Equation 20-302 (Fe_NPend_g), "
                         "Equation 20-306 (target efficiency 0.69)",
    )

    variables = [
        Variable(symbol="Dt_DMIn", name="Dietary dry matter intake", unit="kg/d"),
        Variable(symbol="An_NDF", name="Dietary NDF concentration", unit="% of DM"),
    ]

    formula_text = (
        "Fe_CPend_g = (12.0 + 0.12*NDF%DM) * DMI   [11.62 + 0.134 per Chapter 6 -- see known_discrepancies]\n"
        "Fe_NPend_g = Fe_CPend_g * 0.73\n"
        "Fe_MPendUse_g_Trg = Fe_NPend_g / 0.69"
    )

    assumptions = [
        "Uses the Chapter 20 appendix coefficients (12.0, 0.12), matching the "
        "reference software, rather than Chapter 6's narrative coefficients "
        "(11.62, 0.134) — see known_discrepancies for the ~3% difference this "
        "creates at typical NDF levels.",
        "73% of Fe_CPend is assumed to be true protein (consistent between "
        "Chapter 6 and Chapter 20, no discrepancy on this point).",
        "Target efficiency 0.69, same as scurf, assumed rather than "
        "independently measured for this specific loss pathway.",
    ]

    applicability = (
        "Adult (non-calf) dairy cattle. This is described in the book as the "
        "LARGEST component of 'maintenance' MP — driven by DMI, not truly a "
        "basal-metabolism cost, since it scales with how much the cow eats."
    )

    limitations = [
        "Linear in DMI and NDF%; the book notes this was fit to data from a "
        "specific set of studies and may not extrapolate well to diets far "
        "outside typical NDF ranges.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Chapter 6 (Equation 6-9a): CP-MFP = (11.62 + 0.134*NDF%DM) * DMI. "
        "Chapter 20 appendix (Equation 20-300) and the reference software: "
        "Fe_CPend = (12.0 + 0.12*NDF%DM) * DMI. At NDF=30% DM these differ by "
        "roughly 3% (confirm with actual DMI before assuming this is "
        "negligible for a specific ration). This codebase follows the "
        "appendix/software version for internal consistency with the rest of "
        "the mapped model, but the discrepancy has not been independently "
        "resolved against original source data — flagged, not decided.",
    ]

    def calculate(self, dmi_kg: float, diet_ndf_pct: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        if diet_ndf_pct < 0:
            raise ValueError("diet_ndf_pct cannot be negative")

        import nasem_dairy as nd

        fe_cpend_g = nd.calculate_Fe_CPend_g(
            An_StatePhys="Lactating Cow",
            An_DMIn=dmi_kg,
            An_NDF=diet_ndf_pct,
            Dt_DMIn=dmi_kg,
            Dt_DMIn_ClfLiq=0,
            K_FeCPend_ClfLiq=11.9,  # unused on the non-calf branch
        )
        fe_npend = nd.calculate_Fe_NPend(Fe_CPend=fe_cpend_g / 1000)
        fe_npend_g = nd.calculate_Fe_NPend_g(Fe_NPend=fe_npend)
        km_mp_np_trg = nd.calculate_Km_MP_NP_Trg(
            An_StatePhys="Lactating Cow", coeff_dict={"Kx_MP_NP_Trg": 0.69}
        )
        fe_mpenduse_g = nd.calculate_Fe_MPendUse_g_Trg(
            An_StatePhys="Lactating Cow",
            Fe_CPend_g=fe_cpend_g,
            Fe_NPend_g=fe_npend_g,
            Km_MP_NP_Trg=km_mp_np_trg,
        )

        return EquationResult(
            value=fe_mpenduse_g,
            unit="g/d",
            inputs_used={
                "DMI (kg/d)": dmi_kg,
                "Diet NDF (%)": diet_ndf_pct,
                "Fe_CPend_g (Eq. 20-300)": fe_cpend_g,
                "Fe_NPend_g (Eq. 20-302)": fe_npend_g,
                "Target efficiency Km_MP_NP,Trg": km_mp_np_trg,
            },
            equation=self,
        )
