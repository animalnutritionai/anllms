"""
Urinary endogenous MP — NASEM (2021) Equations 20-294 / 20-295.

    Ur_Nend_g (g/d)  = 0.053 * BW                    [Eq. 20-294]
    Ur_NPend_g (g/d) = Ur_Nend_g * 6.25               [Eq. 20-295]
    Ur_MPendUse_g    = Ur_NPend_g  (efficiency = 1.0, no conversion loss)

Urinary endogenous loss is treated as 100% efficient (NP = MP directly),
unlike scurf and fecal endogenous losses which use the 0.69 target
efficiency. The book is explicit about why: these AAs are lost directly
from blood to urine without a synthesis/conversion step, so there's no
"efficiency of use" to apply.

Chapter 6's underlying literature review derived Ur_Nend from five summed
components (urea, creatinine, creatine, purine derivatives, 3-methyl-His;
Equations 20-287 through 20-293) averaging ~53 mg N/kg BW. The simplified
Equation 20-294 (0.053 x BW) is the form actually used for calculations,
per the book's own statement ("the latter being used for downstream
calculations").
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class UrinaryEndogenousMPNASEM2021(KnowledgeEquation):
    """Urinary endogenous MP requirement (NASEM 2021, Eq. 20-294/20-295)."""

    name = "Urinary endogenous metabolizable protein (MP) requirement"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (derivation) / 20 (appendix formula used)",
        equation_number="Equation 20-294 (Ur_Nend_g) and Equation 20-295 (Ur_NPend_g)",
    )

    variables = [
        Variable(symbol="BW", name="Body weight", unit="kg"),
    ]

    formula_text = (
        "Ur_Nend_g = 0.053 * BW\n"
        "Ur_NPend_g = Ur_Nend_g * 6.25\n"
        "Ur_MPendUse_g = Ur_NPend_g  (100% efficient, no division needed)"
    )

    assumptions = [
        "Efficiency of MP-to-NP conversion for this loss is 1.0 (100%), because "
        "the underlying N compounds (urea, creatinine, 3-methyl-histidine, "
        "etc.) pass from blood to urine directly rather than being "
        "synthesized from absorbed AA — there is no conversion step to be "
        "inefficient at.",
        "Simplified summary coefficient (0.053 g N/kg BW) is used rather than "
        "the five-component detailed derivation (urea + creatinine + creatine "
        "+ purine derivatives + 3-methyl-His); the book states explicitly "
        "that the simplified form is what downstream calculations use.",
        "N-to-protein conversion factor of 6.25 (i.e., protein assumed 16% N) "
        "is applied uniformly, consistent with the rest of the MP system.",
    ]

    applicability = "Adult (non-calf) dairy cattle. Calves use a different equation (2.75*BW_empty^0.50)."

    limitations = [
        "A fixed BW-proportional coefficient; does not vary with diet, breed, "
        "or physiological state beyond calf/non-calf.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")

        import nasem_dairy as nd

        ur_nend_g = nd.calculate_Ur_Nend_g(An_BW=bw_kg)
        ur_npend_g = nd.calculate_Ur_NPend_g(
            An_StatePhys="Lactating Cow", An_BW=bw_kg, Ur_Nend_g=ur_nend_g
        )
        ur_mpenduse_g = nd.calculate_Ur_MPendUse_g(Ur_NPend_g=ur_npend_g)

        return EquationResult(
            value=ur_mpenduse_g,
            unit="g/d",
            inputs_used={
                "BW (kg)": bw_kg,
                "Ur_Nend_g (g N/d, Eq. 20-294)": ur_nend_g,
                "Ur_NPend_g (g NP/d, Eq. 20-295)": ur_npend_g,
            },
            equation=self,
        )
