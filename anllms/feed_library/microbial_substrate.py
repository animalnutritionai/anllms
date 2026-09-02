"""
Microbial-synthesis substrate supply -- wraps the REAL nasem_dairy
diet-level nutrient intake and rumen-digestion functions, replacing the
earlier approach (in scientific/protein/total_mp_supply.py) of running
the FULL nd.nasem() model just to get the inputs
MicrobialCrudeProteinNASEM2021 needs: rumen-degradable protein intake
(An_RDPIn, An_RDP) and rumen-digested NDF/starch intake (Rum_DigNDFIn,
Rum_DigStIn).

WHY THIS IS POSSIBLE WITHOUT A FULL MODEL RUN:
Tracing each of these four values through the real nasem_dairy source
(nasem_equations/rumen.py, nutrient_intakes.py, animal.py) shows none
of them depend on the iterative rumen-fill/pH submodel or any
requirement-side calculation -- they are all direct functions of
diet-total nutrient intakes:

    Dt_CPIn, Dt_NDFIn, Dt_StIn, Dt_ADFIn, Dt_ForWetIn, Dt_ForNDF
        = plain sums (or DM%-weighted sums) of per-feed columns already
          produced by nd.calculate_feed_data() -- the SAME function
          feed_library.rup_supply already calls (via the shared
          feed_library._feed_data.build_complete_feed_data() helper).

    Rum_dcNDF = regression on Dt_DMIn, Dt_NDFIn, Dt_StIn, Dt_CPIn,
                Dt_ADFIn, Dt_ForWet                      [nd.calculate_Rum_dcNDF]
    Rum_dcSt  = regression on Dt_DMIn, Dt_ForNDF, Dt_StIn, Dt_ForWet
                                                          [nd.calculate_Rum_dcSt]
    Rum_DigNDFIn = Rum_dcNDF/100 * Dt_NDFIn              [nd.calculate_Rum_DigNDFIn]
    Rum_DigStIn  = Rum_dcSt/100 * Dt_StIn                [nd.calculate_Rum_DigStIn]

    Dt_RDPIn  = Dt_CPIn - Dt_RUPIn                       [nd.calculate_Dt_RDPIn]
                (Dt_RUPIn reused from feed_library.rup_supply's own
                 real Dt_RUPIn -- not recomputed independently here,
                 avoiding two slightly different RUP numbers existing
                 in the same report)
    An_RDPIn  = Dt_RDPIn + InfRum_RDPIn (=0, no infusions modeled)
                                                          [nd.calculate_An_RDPIn]
    An_RDP    = An_RDPIn / (Dt_DMIn + InfRum_DMIn(=0)) * 100
                                                          [nd.calculate_An_RDP]

Every calculation above calls a real nasem_dairy function directly --
no math is reimplemented here. This module only assembles diet-level
sums from the same complete_feed_data DataFrame rup_supply.py already
produces, then feeds them through the four real functions listed above.

Book citation: NASEM (2021) Chapter 6 ("Rumen Fermentation" / RDP
supply and rumen NDF/starch digestion discussion) and Chapter 20
appendix, Eq. 20-54 (Rum_dcNDF), Eq. 20-55 (Rum_dcSt). Dt_RDPIn /
An_RDPIn / An_RDP are diet-composition bookkeeping (CP minus RUP, plus
infusions), not separately display-numbered.

This does NOT run the full nd.nasem() model. This module is data-layer
plumbing (like rup_supply.py), not a citable single-formula
KnowledgeEquation in its own right -- callers needing a citation-bearing
equation object should build on scientific/protein/microbial_crude_protein.py's
MicrobialCrudeProteinNASEM2021, which is where these values get used.
"""

from __future__ import annotations

from dataclasses import dataclass

from anllms.feed_library._feed_data import build_complete_feed_data
from anllms.feed_library.ration import Ration


@dataclass
class MicrobialSubstrateResult:
    """
    Diet-level inputs MicrobialCrudeProteinNASEM2021.calculate() needs,
    computed independently (no full model run).
    """

    an_rdpin_kg: float      # An_RDPIn, kg/d -- rumen-degradable protein intake
    an_rdp_pct: float       # An_RDP, % of DM -- used only to decide the 12%-DMI cap
    rum_digndfin_kg: float  # Rum_DigNDFIn, kg/d -- rumen-digested NDF intake
    rum_digstin_kg: float   # Rum_DigStIn, kg/d -- rumen-digested starch intake

    # Surfaced for transparency / debugging, since they're intermediate
    # values in the same real chain:
    dt_rdpin_kg: float       # Dt_RDPIn, kg/d (diet-only, before infusions)
    dt_cpin_kg: float        # Dt_CPIn, kg/d
    dt_rupin_kg: float       # Dt_RUPIn, kg/d (reused, not recomputed)
    rum_dcndf_pct: float     # Rum_dcNDF, % -- rumen NDF digestion coefficient
    rum_dcst_pct: float      # Rum_dcSt, % -- rumen starch digestion coefficient


def compute_microbial_substrate(
    ration: Ration,
    dmi_kg: float,
    an_state_phys: str = "Lactating Cow",
    use_dndf_iv: int = 0,
) -> MicrobialSubstrateResult:
    """
    Computes the four diet-level substrate values
    MicrobialCrudeProteinNASEM2021 needs (An_RDPIn, An_RDP,
    Rum_DigNDFIn, Rum_DigStIn) for a Ration, using real nasem_dairy
    diet-intake and rumen-digestion functions directly -- no full
    nd.nasem() model run.

    dmi_kg: the diet's actual dry matter intake (kg/d). Callers should
    pass the same DMI value used elsewhere in a given report (matching
    rup_supply.py's and total_mp_supply.py's DMIn_eqn=0 convention --
    this is NOT re-predicted here).

    an_state_phys / use_dndf_iv: same meaning and defaults as
    rup_supply.compute_rup_supply() -- see that module's docstring.

    No infusions are modeled anywhere in this codebase (see
    simulation/animal_state.py), so InfRum_RDPIn and InfRum_DMIn are
    both treated as 0 -- consistent with the rest of this project.
    """
    complete_feed_data = build_complete_feed_data(
        ration=ration, dmi_kg=dmi_kg, an_state_phys=an_state_phys, use_dndf_iv=use_dndf_iv
    )

    import nasem_dairy as nd

    dt_cpin_kg = nd.calculate_Dt_CPIn(complete_feed_data["Fd_CPIn"])
    dt_ndfin_kg = nd.calculate_Dt_NDFIn(complete_feed_data["Fd_NDFIn"])
    dt_stin_kg = nd.calculate_Dt_StIn(complete_feed_data["Fd_StIn"])
    dt_adfin_kg = nd.calculate_Dt_ADFIn(complete_feed_data["Fd_ADFIn"])
    dt_forwetin_kg = complete_feed_data["Fd_ForWetIn"].sum()
    dt_forwet_pct = nd.calculate_Dt_ForWet(dt_forwetin_kg, dmi_kg)
    dt_forndf_pct = nd.calculate_Dt_ForNDF(
        complete_feed_data["Fd_DMInp"], complete_feed_data["Fd_ForNDF"]
    )

    dt_rupin_kg = nd.calculate_Dt_RUPIn(complete_feed_data["Fd_RUPIn"])
    dt_rdpin_kg = nd.calculate_Dt_RDPIn(dt_cpin_kg, dt_rupin_kg)
    an_rdpin_kg = nd.calculate_An_RDPIn(dt_rdpin_kg, InfRum_RDPIn=0.0)
    an_rdp_pct = nd.calculate_An_RDP(an_rdpin_kg, dmi_kg, InfRum_DMIn=0.0)

    rum_dcndf_pct = nd.calculate_Rum_dcNDF(
        Dt_DMIn=dmi_kg,
        Dt_NDFIn=dt_ndfin_kg,
        Dt_StIn=dt_stin_kg,
        Dt_CPIn=dt_cpin_kg,
        Dt_ADFIn=dt_adfin_kg,
        Dt_ForWet=dt_forwet_pct,
    )
    rum_dcst_pct = nd.calculate_Rum_dcSt(
        Dt_DMIn=dmi_kg,
        Dt_ForNDF=dt_forndf_pct,
        Dt_StIn=dt_stin_kg,
        Dt_ForWet=dt_forwet_pct,
    )
    rum_digndfin_kg = nd.calculate_Rum_DigNDFIn(rum_dcndf_pct, dt_ndfin_kg)
    rum_digstin_kg = nd.calculate_Rum_DigStIn(rum_dcst_pct, dt_stin_kg)

    return MicrobialSubstrateResult(
        an_rdpin_kg=float(an_rdpin_kg),
        an_rdp_pct=float(an_rdp_pct),
        rum_digndfin_kg=float(rum_digndfin_kg),
        rum_digstin_kg=float(rum_digstin_kg),
        dt_rdpin_kg=float(dt_rdpin_kg),
        dt_cpin_kg=float(dt_cpin_kg),
        dt_rupin_kg=float(dt_rupin_kg),
        rum_dcndf_pct=float(rum_dcndf_pct),
        rum_dcst_pct=float(rum_dcst_pct),
    )
