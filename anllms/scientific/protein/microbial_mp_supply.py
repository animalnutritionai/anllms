"""
Metabolizable protein (MP) supply from ruminal microbial protein — NASEM (2021).

Not separately display-numbered in the Chapter 20 appendix as a single
equation (the appendix jumps from Eq. 20-79 to Eq. 20-80 without a
numbered display equation for this specific step — see
known_discrepancies), but explicitly described in Chapter 6 narrative text
and implemented identically in the reference software:

    Du_idMiCP_g (g/d) = Du_MiCP_g * 0.80        [SI_dcMiCP: intestinal
                                                   digestibility of MCP]
    Du_idMiTP_g (g/d) = Du_idMiCP_g * 0.824      [fMiTP_MiCP: TP fraction
                                                   of digestible MCP]

Combined, this means only 0.80 * 0.824 = 65.9% of microbial crude protein
synthesized in the rumen ultimately becomes MP supply to the cow — a
figure the book states explicitly in prose ("the conversion of MCP to MP
is assumed to be 82.4 percent TP in CP at 80 percent digestibility = 65.9
percent"), which this equation's calculate() reproduces via the two
separate multiplications, not a hardcoded 0.659 shortcut, so each factor
stays independently traceable to its own coefficient and source.

This IS the microbial contribution to MP supply. Total MP supply also
requires digestible RUP (rumen-undegraded protein that escapes ruminal
fermentation) — a separate, not-yet-mapped source — see known_discrepancies.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.scientific.protein.microbial_crude_protein import MicrobialCrudeProteinNASEM2021


class MicrobialMPSupplyNASEM2021(KnowledgeEquation):
    """MP supply from digestible microbial true protein (NASEM 2021, Chapter 6 narrative; software Du_idMiTP_g)."""

    name = "Metabolizable protein (MP) supply from ruminal microbial protein"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6",
        section="Protein and Amino Acid Requirements > Microbial Protein Supply",
        equation_number="Not separately display-numbered in the Chapter 20 appendix "
                         "(see known_discrepancies); coefficients (80% digestibility, "
                         "82.4% TP/CP) stated explicitly in Chapter 6 narrative text",
    )

    variables = [
        Variable(symbol="Du_MiCP_g", name="Ruminal microbial crude protein synthesized", unit="g/d",
                  description="From MicrobialCrudeProteinNASEM2021."),
    ]

    formula_text = (
        "Du_idMiCP_g = Du_MiCP_g * 0.80   (SI_dcMiCP: intestinal digestibility)\n"
        "Du_idMiTP_g = Du_idMiCP_g * 0.824 (fMiTP_MiCP: TP fraction)\n"
        "Combined: 65.9% of MCP becomes MP supply"
    )

    assumptions = [
        "80% small-intestinal digestibility of microbial crude protein — the "
        "book notes some studies suggest true digestibility may be higher "
        "(81-87%), but the committee retained the 80% figure used since "
        "NRC (1985) due to limited dairy-specific data.",
        "82.4% true-protein fraction of microbial CP — revised upward from "
        "NRC (2001)'s 80% based on a broader literature survey (Sok et al., "
        "2017) of bacterial AA composition; the remaining ~17.6% is mostly "
        "nucleic acids, not usable protein.",
        "Combined 65.9% MCP-to-MP conversion is slightly higher than NRC "
        "(2001)'s 64%, driven entirely by the TP fraction revision (82.4% "
        "vs 80%), not a digestibility change.",
    ]

    applicability = "Any dairy cattle diet with a computed ruminal microbial crude protein synthesis value."

    limitations = [
        "Fixed coefficients regardless of diet type — does not vary "
        "digestibility or TP fraction by forage:concentrate ratio, ionophore "
        "use, or other factors known to influence rumen microbial ecology.",
        "Represents an average across bacteria; protozoal and fungal protein "
        "(known to have somewhat different digestibility) are not modeled "
        "separately.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "No distinct display-equation number was found in the Chapter 20 "
        "appendix for this specific idMiCP/idMiTP conversion step (the "
        "appendix numbering goes directly from Equation 20-79 to Equation "
        "20-80). The coefficients themselves (80%, 82.4%) are stated "
        "explicitly in Chapter 6 narrative prose and confirmed via the "
        "reference software's default coeff_dict and fixture test cases, "
        "so the VALUES are verified even though a single display-equation "
        "number for this exact step is not.",
        "This equation gives MP supply from MICROBIAL protein only. Total MP "
        "supply = this + digestible RUP (rumen-undegraded protein escaping "
        "fermentation) + digestible endogenous protein contributions. RUP "
        "supply is NOT yet mapped in this codebase — it depends on "
        "feed-library-level RUP digestibility values per ingredient, which "
        "is a substantial additional scope (see project notes on feed "
        "library integration).",
    ]

    notes = (
        "This is one of (at least) two MP supply sources needed for a real "
        "requirement-vs-supply check. RUP-derived MP supply is the next gap "
        "to close before diet evaluation/optimization can compare total "
        "supply against MPMaintenanceRequirementNASEM2021 + "
        "MilkMPRequirementNASEM2021."
    )

    def calculate(
        self,
        rdp_intake_kg: float,
        diet_rdp_pct: float,
        dmi_kg: float,
        rumen_digested_ndf_kg: float,
        rumen_digested_starch_kg: float,
    ) -> EquationResult:
        micp_result = MicrobialCrudeProteinNASEM2021().calculate(
            rdp_intake_kg=rdp_intake_kg,
            diet_rdp_pct=diet_rdp_pct,
            dmi_kg=dmi_kg,
            rumen_digested_ndf_kg=rumen_digested_ndf_kg,
            rumen_digested_starch_kg=rumen_digested_starch_kg,
        )

        import nasem_dairy as nd

        du_idmicp_g = nd.calculate_Du_idMiCP_g(
            Du_MiCP_g=micp_result.value, coeff_dict={"SI_dcMiCP": 80}
        )
        du_idmitp_g = nd.calculate_Du_idMiTP_g(
            Du_idMiCP_g=du_idmicp_g, coeff_dict={"fMiTP_MiCP": 0.824}
        )

        return EquationResult(
            value=du_idmitp_g,
            unit="g/d",
            inputs_used={
                "Ruminal MCP synthesized (g/d)": micp_result.value,
                "Digestible MCP (g/d, x0.80)": du_idmicp_g,
                "Digestible microbial TP / MP supply (g/d, x0.824)": du_idmitp_g,
            },
            equation=self,
        )
