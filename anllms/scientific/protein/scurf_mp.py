"""
Scurf (skin/hair) MP requirement — NASEM (2021) Equations 20-283/20-284,
divided by the 0.69 target efficiency (Eq. 20-306).

    Scrf_CP_g (g/d) = 0.20 * BW^0.60                  [Eq. 20-283]
    Scrf_TP_g (g/d) = Scrf_CP_g * 0.86                [Eq. 20-284, appendix]
    Scrf_MPUse_g_Trg = Scrf_TP_g / 0.69

CONFIRMED BOOK-INTERNAL DISCREPANCY (found by comparing Chapter 6's
narrative text against Chapter 20's appendix formula, not by comparing to
the reference software): Chapter 6 states the CP-to-TP conversion factor
for scurf as 0.85 ("NP-scurf (g/d) = 0.20 x BW^0.60 x 0.85 = 0.17 x BW^0.60",
Equation 6-7a), while the Chapter 20 appendix (Equation 20-284) states
0.86. The reference software uses 0.86 (confirmed against its default
coeff_dict and a fixture test case: Scrf_CP_g=7 -> Scrf_NP_g=6.02, which is
7*0.86, not 7*0.85=5.95). This equation follows the software/appendix value
(0.86) for consistency with the rest of the mapped model, but the
discrepancy is real and unresolved — see known_discrepancies.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class ScurfMPNASEM2021(KnowledgeEquation):
    """Scurf MP requirement (NASEM 2021, Eq. 20-283/20-284, target efficiency Eq. 20-306)."""

    name = "Scurf (skin/hair) metabolizable protein (MP) requirement"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (derivation, Eq. 6-7a) / 20 (appendix, Eq. 20-283/20-284/20-306)",
        equation_number="Equation 20-283 (Scrf_CP_g), Equation 20-284 (Scrf_TP_g), "
                         "Equation 20-306 (target efficiency 0.69)",
    )

    variables = [
        Variable(symbol="BW", name="Body weight", unit="kg"),
    ]

    formula_text = (
        "Scrf_CP_g = 0.20 * BW^0.60\n"
        "Scrf_TP_g = Scrf_CP_g * 0.86   [0.85 per Chapter 6 narrative -- see known_discrepancies]\n"
        "Scrf_MPUse_g_Trg = Scrf_TP_g / 0.69"
    )

    assumptions = [
        "CP-to-TP conversion factor of 0.86 used (appendix/software value), "
        "not the 0.85 stated in Chapter 6's narrative text — see "
        "known_discrepancies. The numeric difference is small (~1%) but is "
        "not zero and should not be presented as fully resolved.",
        "Target efficiency of MP-to-NP conversion for scurf (0.69) is assumed "
        "equal to the target efficiency used for milk protein and metabolic "
        "fecal protein — this is a modeling choice by the committee, not an "
        "independently measured scurf-specific efficiency.",
    ]

    applicability = "Adult (non-calf) dairy cattle. Calves use a different CP-to-BW coefficient (0.219 vs 0.20)."

    limitations = [
        "A fixed allometric (BW^0.60) relationship derived from Beltsville "
        "calorimetry data; does not vary with hair coat, season, or breed.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Chapter 6 (Equation 6-7a) states the scurf CP-to-TP ratio as 0.85. "
        "Chapter 20's appendix (Equation 20-284) and the reference software's "
        "default coeff_dict both use 0.86. This was confirmed against a real "
        "fixture test case (Scrf_CP_g=7 -> Scrf_NP_g=6.02 = 7*0.86), not "
        "assumed. This codebase follows 0.86 for consistency with the mapped "
        "software, but this is a genuine unresolved discrepancy within the "
        "primary source itself, not a book-vs-software conflict — flagging "
        "rather than picking one as definitively 'correct.'",
    ]

    def calculate(self, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")

        import nasem_dairy as nd

        scrf_cp_g = nd.calculate_Scrf_CP_g(An_StatePhys="Lactating Cow", An_BW=bw_kg)
        scrf_np_g = nd.calculate_Scrf_NP_g(Scrf_CP_g=scrf_cp_g, coeff_dict={"Body_NP_CP": 0.86})
        km_mp_np_trg = nd.calculate_Km_MP_NP_Trg(
            An_StatePhys="Lactating Cow", coeff_dict={"Kx_MP_NP_Trg": 0.69}
        )
        scrf_mpuse_g = nd.calculate_Scrf_MPUse_g_Trg(
            An_StatePhys="Lactating Cow",
            Scrf_CP_g=scrf_cp_g,
            Scrf_NP_g=scrf_np_g,
            Km_MP_NP_Trg=km_mp_np_trg,
        )

        return EquationResult(
            value=scrf_mpuse_g,
            unit="g/d",
            inputs_used={
                "BW (kg)": bw_kg,
                "Scrf_CP_g (Eq. 20-283)": scrf_cp_g,
                "Scrf_NP_g (Eq. 20-284, using 0.86)": scrf_np_g,
                "Target efficiency Km_MP_NP,Trg": km_mp_np_trg,
            },
            equation=self,
        )
