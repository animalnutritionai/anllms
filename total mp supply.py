"""
Total metabolizable protein (MP) supply from the diet — microbial + RUP.

UPDATE (this revision): BOTH halves of this equation are now sourced
independently -- neither requires a full nasem_dairy.nasem() model run
anymore.

The RUP half is computed via feed_library.rup_supply.compute_rup_supply(),
which wraps the real per-feed RUP-kinetics pipeline (nd.get_feed_data()
-> nd.calculate_feed_data() -> nd.calculate_Dt_idRUPIn()) directly. This
was verified to match the full model's own Dt_idRUPIn to rel_tol=1e-6 on
the real lactating_cow_test demo scenario (see tests/test_rup_supply.py)
before being wired in here.

The MICROBIAL half is now computed via
feed_library.microbial_substrate.compute_microbial_substrate(), which
independently derives the four inputs MicrobialCrudeProteinNASEM2021
needs (An_RDPIn, An_RDP, Rum_DigNDFIn, Rum_DigStIn) from the same
per-feed pipeline (see that module's docstring for the full derivation
-- none of these four values depend on the iterative rumen-fill/pH
submodel, only on diet-total nutrient intake sums, so no full model run
is needed). This closes the scope gap this docstring previously
documented. Verified to match the full model's own Du_idMiTP_g to
rel_tol=1e-6 on the real lactating_cow_test demo scenario (see
tests/test_total_mp_supply.py) before being wired in here.

model_output / run_full_model() remain supported as an OPTIONAL
override (see calculate()'s docstring) for callers that already have a
full model run available for other reasons and want to cross-check
against it -- not because either half requires it anymore.

Book citation for the underlying RUP kinetics (now independently
computed, not full-model-derived): NASEM (2021) Chapter 6 ("Ruminal
Protein Degradation" / RDP-RUP discussion) and Chapter 19 (the
electronic feed library providing per-ingredient A/B/C fractions and
Kd). No single equation number covers the full chain -- it is a kinetic
system built from many equations together (see Chapter 6 narrative
description of the first-order A/B/C/Kd/Kp model), not one formula.

WHAT THIS TAKES AS INPUT: a Ration built from real feed library
ingredients and a DMI value. DMI is NOT re-predicted by this equation --
the caller's own dmi_kg is passed through directly to both the RUP and
microbial-substrate pipelines, so this stays consistent with whichever
DMI equation (Eq. 2-1 or 2-2) the rest of the report used. `animal` and
`milk` parameters are still accepted (unchanged call signature, so
existing callers like requirements_report.py don't need updating) but
are no longer required for the calculation itself -- they are only used
if a caller explicitly needs backward-compatible access to them; the
independent path below does not touch either.

model_output is now OPTIONAL and used only as a cross-check, not a
requirement: if a caller already has a full model run available (e.g.
requirements_report.py, which runs one anyway for other requirement/
supply figures), this equation compares its own independently-computed
Du_idMiTP_g against the full model's own value and surfaces the
difference in inputs_used -- it does NOT fall back to the full model's
number as the primary answer anymore.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.feed_library.microbial_substrate import compute_microbial_substrate
from anllms.feed_library.ration import Ration
from anllms.feed_library.rup_supply import compute_rup_supply
from anllms.scientific.protein.microbial_mp_supply import MicrobialMPSupplyNASEM2021
from anllms.simulation.animal_state import AnimalState, MilkTarget


class TotalMPSupplyNASEM2021(KnowledgeEquation):
    """Total MP supply from the diet: independently-computed RUP + independently-computed microbial (NASEM 2021)."""

    name = "Total metabolizable protein (MP) supply from the diet (microbial + RUP)"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (RDP/RUP kinetics narrative, rumen NDF/starch digestion, "
                "microbial protein synthesis) / 19 (electronic feed library, "
                "per-ingredient A/B/C fractions and Kd) / 20 (appendix, "
                "Eq. 20-54/20-55 rumen digestion coefficients)",
        equation_number="No single equation number -- a chained system of "
                         "several real functions; see this module's and "
                         "feed_library.microbial_substrate's docstrings for "
                         "the full derivation",
    )

    variables = [
        Variable(symbol="user_diet", name="Ration (ingredient names + kg DM/d)", unit="n/a"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake (passed through, not re-predicted)", unit="kg/d"),
    ]

    formula_text = "An_MPIn (kg/d) = Du_idMiTP_g/1000 + Dt_idRUPIn  (microbial + RUP contributions)"

    assumptions = [
        "DMI is passed through from the caller (dmi_kg directly, to both "
        "the RUP and microbial-substrate pipelines), not re-predicted -- "
        "keeps this consistent with whichever DMI equation (Eq. 2-1 or "
        "2-2) produced the DMI value used elsewhere in a given report.",
        "No infusions are modeled anywhere in this codebase, so the "
        "microbial substrate calculation treats InfRum_RDPIn and "
        "InfRum_DMIn as 0 -- see feed_library.microbial_substrate's "
        "docstring.",
    ]

    applicability = (
        "Any lactating dairy cow with a defined ration built from real feed "
        "library ingredients (via feed_library.ration.Ration) and a known "
        "DMI value."
    )

    limitations = [
        "Both halves are now traceable to specific real nasem_dairy "
        "function calls with all of their own inputs independently "
        "sourced -- the RUP half via feed_library.rup_supply, the "
        "microbial half via feed_library.microbial_substrate + "
        "MicrobialMPSupplyNASEM2021. Both give a debugging breakdown "
        "(RUPSupplyResult.fd_idrupin_kg; MicrobialSubstrateResult's "
        "intermediate fields).",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "RUP-derived MP supply is sourced independently via "
        "feed_library.rup_supply.compute_rup_supply(), not from a full "
        "model run. Verified to match the full model's own Dt_idRUPIn to "
        "rel_tol=1e-6 on the real lactating_cow_test demo scenario "
        "(tests/test_rup_supply.py).",
        "Microbial-derived MP supply (Du_idMiTP_g) is now ALSO sourced "
        "independently, via feed_library.microbial_substrate."
        "compute_microbial_substrate() feeding MicrobialMPSupplyNASEM2021 "
        "-- this closes the gap this docstring previously documented "
        "(the four inputs An_RDPIn/An_RDP/Rum_DigNDFIn/Rum_DigStIn were "
        "not independently mapped; they now are). Verified to match the "
        "full model's own Du_idMiTP_g to rel_tol=1e-6 on the real "
        "lactating_cow_test demo scenario (tests/test_total_mp_supply.py). "
        "If a caller passes model_output, this equation still cross-checks "
        "against the full model's own value and surfaces any discrepancy "
        "in inputs_used -- kept as an ongoing sanity check, not because "
        "either half depends on it.",
    ]

    def calculate(
        self,
        animal: AnimalState = None,
        milk: MilkTarget = None,
        ration: Ration = None,
        dmi_kg: float = None,
        model_output=None,
    ) -> EquationResult:
        """
        Both RUP-derived and microbial-derived MP supply are computed
        independently -- no full model run needed for either half.

        `animal` and `milk` are accepted for backward-compatible call
        signatures (e.g. requirements_report.py's existing call site) but
        are not used by the independent calculation path.

        If model_output is provided (a ModelOutput from a prior
        run_full_model() call, e.g. one already run by RequirementsReport
        for other requirement/supply figures), it is used ONLY as a
        cross-check against the independently-computed Du_idMiTP_g -- the
        returned total_mp_supply_g always comes from the independent
        calculation, not from model_output.
        """
        if ration is None or dmi_kg is None:
            raise ValueError("ration and dmi_kg are required")

        rup_result = compute_rup_supply(ration=ration, dmi_kg=dmi_kg)
        dt_idrupin_kg = rup_result.dt_idrupin_kg

        substrate = compute_microbial_substrate(ration=ration, dmi_kg=dmi_kg)
        microbial_result = MicrobialMPSupplyNASEM2021().calculate(
            rdp_intake_kg=substrate.an_rdpin_kg,
            diet_rdp_pct=substrate.an_rdp_pct,
            dmi_kg=dmi_kg,
            rumen_digested_ndf_kg=substrate.rum_digndfin_kg,
            rumen_digested_starch_kg=substrate.rum_digstin_kg,
        )
        du_idmitp_g = microbial_result.value

        cross_check = None
        if model_output is not None:
            full_model_du_idmitp_g = model_output.get_value("Du_idMiTP_g")
            diff_g = du_idmitp_g - full_model_du_idmitp_g
            pct_diff = (
                abs(diff_g) / full_model_du_idmitp_g * 100
                if full_model_du_idmitp_g
                else float("nan")
            )
            cross_check = {
                "Full model's Du_idMiTP_g (g/d)": full_model_du_idmitp_g,
                "Independent vs. full model difference (g/d)": diff_g,
                "Independent vs. full model difference (%)": pct_diff,
            }

        total_mp_supply_g = du_idmitp_g + (dt_idrupin_kg * 1000)

        inputs_used = {
            "DMI (kg/d, passed through)": dmi_kg,
            "Microbial MP supply (g/d, Du_idMiTP_g, independently computed)": du_idmitp_g,
            "Microbial substrate inputs (An_RDPIn kg/d, An_RDP %DM, "
            "Rum_DigNDFIn kg/d, Rum_DigStIn kg/d)": {
                "An_RDPIn": substrate.an_rdpin_kg,
                "An_RDP": substrate.an_rdp_pct,
                "Rum_DigNDFIn": substrate.rum_digndfin_kg,
                "Rum_DigStIn": substrate.rum_digstin_kg,
            },
            "RUP-derived MP supply (g/d, independently computed via "
            "feed_library.rup_supply, x1000)": dt_idrupin_kg * 1000,
            "Per-feed RUP-derived MP supply (g/d)": {
                name: kg * 1000 for name, kg in rup_result.fd_idrupin_kg.items()
            },
            "Ration": list(zip(ration.feedstuffs, ration.kg_dm_per_day)),
        }
        if cross_check is not None:
            inputs_used["Full-model cross-check (optional, not the source of the returned value)"] = cross_check

        return EquationResult(
            value=total_mp_supply_g,
            unit="g/d",
            inputs_used=inputs_used,
            equation=self,
        )
