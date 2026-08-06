"""
Ruminal microbial nitrogen (crude protein) synthesis — NASEM (2021)
Equations 20-74, 20-75, 20-76.

    RDPIn_MiNmax = An_RDPIn if An_RDP <= 12% DM, else Dt_DMIn * 0.12
                   [caps the RDP "seen" by the model at 12% of DMI, since
                    the committee found no additional microbial response
                    above 12% dietary RDP]
    MiN_Vm (g/d)  = 100.8 + 81.56 * RDPIn_MiNmax           [Eq. 20-75]
    Du_MiN_g (g/d) = MiN_Vm / (1 + 0.0939/Rum_DigNDFIn + 0.0274/Rum_DigStIn)
                     ...capped at An_RDPIn_g / 6.25          [Eq. 20-74]
    Du_MiCP_g (g/d) = Du_MiN_g * 6.25                        [Eq. 20-76]

This is a Michaelis-Menten-style saturation model: microbial growth
(MiN_Vm, the "maximum velocity" term) increases with RDP supply, but actual
synthesis (Du_MiN_g) is also constrained by how much rumen-fermentable
carbohydrate (digested NDF and starch) is available to fuel microbial
growth — protein alone doesn't determine microbial yield.

SCOPE NOTE: this equation takes Rum_DigNDFIn, Rum_DigStIn, and An_RDPIn as
direct inputs. In the full model these are themselves predicted by earlier
equations (rumen NDF/starch digestion, Eq. 20-54/20-55; RDP supply from the
diet, Eq. 20-69) that are NOT yet mapped in this codebase — see
known_discrepancies. Treat this as the "given rumen-available substrate,
here is microbial yield" step, not a full farm-diet-to-microbial-protein
pipeline yet.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class MicrobialCrudeProteinNASEM2021(KnowledgeEquation):
    """Ruminal microbial crude protein synthesis (NASEM 2021, Eq. 20-74/20-75/20-76)."""

    name = "Ruminal microbial crude protein (MCP) synthesis"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (derivation) / 20 (appendix, Eq. 20-74/20-75/20-76)",
        equation_number="Equation 20-74 (Du_MiN_g), Equation 20-75 (MiN_Vm), "
                         "Equation 20-76 (Du_MiCP_g)",
    )

    variables = [
        Variable(symbol="An_RDPIn", name="Rumen-degradable protein intake", unit="kg/d"),
        Variable(symbol="An_RDP", name="Dietary RDP concentration", unit="% of DM",
                  description="Used only to decide whether to cap RDPIn_MiNmax."),
        Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d"),
        Variable(symbol="Rum_DigNDFIn", name="Rumen-digested NDF intake", unit="kg/d"),
        Variable(symbol="Rum_DigStIn", name="Rumen-digested starch intake", unit="kg/d"),
    ]

    formula_text = (
        "RDPIn_MiNmax = An_RDPIn if An_RDP<=12% else Dt_DMIn*0.12\n"
        "MiN_Vm = 100.8 + 81.56*RDPIn_MiNmax\n"
        "Du_MiN_g = MiN_Vm / (1 + 0.0939/Rum_DigNDFIn + 0.0274/Rum_DigStIn), "
        "capped at An_RDPIn_g/6.25\n"
        "Du_MiCP_g = Du_MiN_g * 6.25"
    )

    assumptions = [
        "Committee found no additional microbial synthesis response above "
        "12% dietary RDP — RDP intake is capped at 12% of DMI for the "
        "purposes of this equation specifically (RDPIn_MiNmax), even if the "
        "diet's actual RDP% is higher.",
        "Microbial yield is jointly limited by degradable protein AND "
        "fermentable carbohydrate (NDF + starch digested in the rumen) — a "
        "diet can be RDP-adequate and still under-produce microbial protein "
        "if rumen-fermentable carbohydrate is insufficient, or vice versa.",
        "Final output is hard-capped at An_RDPIn_g / 6.25 — microbial N "
        "synthesis cannot exceed the N supplied by RDP intake, a mass-balance "
        "constraint applied regardless of what the saturation curve predicts.",
    ]

    applicability = (
        "Any dairy cattle diet with known/estimated RDP intake, rumen-"
        "digested NDF intake, and rumen-digested starch intake. This "
        "replaced the simpler NRC (2001) TDN-based approach (Du_MiN_NRC2001_g "
        "= 13% x TDN) as the current default model."
    )

    limitations = [
        "Empirical saturation-kinetics model; extrapolation to diets with "
        "very low or very high digestible NDF/starch (near zero in the "
        "denominator) can behave unstably — division by Rum_DigNDFIn or "
        "Rum_DigStIn near zero is undefined.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Rum_DigNDFIn and Rum_DigStIn (rumen-digested NDF/starch intake) and "
        "An_RDPIn (RDP supply) are accepted here as direct inputs. In the "
        "full NASEM model these are themselves predicted by earlier chained "
        "equations (rumen NDF/starch digestion kinetics, Eq. 20-54/20-55; "
        "dietary RDP supply, Eq. 20-69) that are NOT yet mapped as knowledge "
        "objects in this codebase. Values passed to this equation must "
        "currently come from feed-library-level calculations done outside "
        "this platform (e.g., via the reference software directly) until "
        "those upstream equations are mapped.",
    ]

    def calculate(
        self,
        rdp_intake_kg: float,
        diet_rdp_pct: float,
        dmi_kg: float,
        rumen_digested_ndf_kg: float,
        rumen_digested_starch_kg: float,
    ) -> EquationResult:
        if rdp_intake_kg < 0:
            raise ValueError("rdp_intake_kg cannot be negative")
        if rumen_digested_ndf_kg <= 0 or rumen_digested_starch_kg <= 0:
            raise ValueError(
                "rumen_digested_ndf_kg and rumen_digested_starch_kg must be "
                "positive (used as divisors in the saturation-kinetics formula)"
            )

        import nasem_dairy as nd

        rdpin_mimax = nd.calculate_RDPIn_MiNmax(
            Dt_DMIn=dmi_kg, An_RDP=diet_rdp_pct, An_RDPIn=rdp_intake_kg
        )
        min_vm = nd.calculate_MiN_Vm(
            RDPIn_MiNmax=rdpin_mimax,
            coeff_dict={"VmMiNInt": 100.8, "VmMiNRDPSlp": 81.56},
        )
        du_min_g = nd.calculate_Du_MiN_NRC2021_g(
            MiN_Vm=min_vm,
            Rum_DigNDFIn=rumen_digested_ndf_kg,
            Rum_DigStIn=rumen_digested_starch_kg,
            An_RDPIn_g=rdp_intake_kg * 1000,
            coeff_dict={"KmMiNRDNDF": 0.0939, "KmMiNRDSt": 0.0274},
        )
        du_micp_g = nd.calculate_Du_MiCP_g(Du_MiN_g=du_min_g)

        return EquationResult(
            value=du_micp_g,
            unit="g/d",
            inputs_used={
                "RDP intake (kg/d)": rdp_intake_kg,
                "Diet RDP (%DM)": diet_rdp_pct,
                "DMI (kg/d)": dmi_kg,
                "Rumen-digested NDF (kg/d)": rumen_digested_ndf_kg,
                "Rumen-digested starch (kg/d)": rumen_digested_starch_kg,
                "RDPIn_MiNmax (Eq. cap logic)": rdpin_mimax,
                "MiN_Vm (g/d, Eq. 20-75)": min_vm,
                "Du_MiN_g (g/d, Eq. 20-74)": du_min_g,
            },
            equation=self,
        )
