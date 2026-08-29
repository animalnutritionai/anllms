"""
Total metabolizable protein (MP) supply from the diet — microbial + RUP.

UPDATE (this revision): the RUP half of this equation is no longer
sourced from a full nasem_dairy.nasem() model run. It is now computed
independently via feed_library.rup_supply.compute_rup_supply(), which
wraps the real per-feed RUP-kinetics pipeline (nd.get_feed_data() ->
nd.calculate_feed_data() -> nd.calculate_Dt_idRUPIn()) directly, without
running the full model. This was verified to match the full model's own
Dt_idRUPIn to rel_tol=1e-6 on the real lactating_cow_test demo scenario
(see tests/test_rup_supply.py) before being wired in here.

The MICROBIAL half (Du_idMiTP_g) still requires a full model run. This
is NOT the same scope gap as before -- it's a separate, narrower one:
MicrobialCrudeProteinNASEM2021 (the underlying microbial synthesis
equation) itself documents that its own inputs -- rumen-degradable
protein intake, rumen-digested NDF intake, rumen-digested starch intake
-- are produced by earlier equations (RDP supply, rumen NDF/starch
digestion) not yet independently mapped in this codebase. Until those
are mapped, the full model remains the only source for Du_idMiTP_g in a
way consistent with the rest of a given report's inputs.

SCOPE DECISION for the still-outstanding microbial half, stated
explicitly rather than hidden: every other equation in this codebase
wraps ONE (or a small handful of) specific, citable nasem_dairy
function(s) with all of ITS inputs independently sourced. The microbial
half doesn't yet meet that bar -- MicrobialMPSupplyNASEM2021 itself is
independently citable and correctly wraps real functions, but the
values it needs (Rum_DigNDFIn, Rum_DigStIn, An_RDPIn) are not yet
available from this codebase without a full model run.

Book citation for the underlying RUP kinetics (now independently
computed, not full-model-derived): NASEM (2021) Chapter 6 ("Ruminal
Protein Degradation" / RDP-RUP discussion) and Chapter 19 (the
electronic feed library providing per-ingredient A/B/C fractions and
Kd). No single equation number covers the full chain -- it is a kinetic
system built from many equations together (see Chapter 6 narrative
description of the first-order A/B/C/Kd/Kp model), not one formula.

WHAT THIS TAKES AS INPUT: a full AnimalState (including the
previously-optional gestation/breed/environment fields, still required
here since the full model is still needed for the microbial half) and a
Ration built from real feed library ingredients. DMI is NOT re-predicted
by this equation -- the caller's own DMI value is passed through
directly (DMIn_eqn=0 in the full-model path; the independent RUP path
takes dmi_kg directly), so this stays consistent with whichever DMI
equation (Eq. 2-1 or 2-2) the rest of the report used.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.feed_library.ration import Ration
from anllms.feed_library.rup_supply import compute_rup_supply
from anllms.simulation.animal_state import AnimalState, MilkTarget


class TotalMPSupplyNASEM2021(KnowledgeEquation):
    """Total MP supply from the diet: independently-computed RUP + full-model microbial (NASEM 2021)."""

    name = "Total metabolizable protein (MP) supply from the diet (microbial + RUP)"

    citation = Citation(
        publication=NASEM_DAIRY_2021,
        chapter="6 (RDP/RUP kinetics narrative) / 19 (electronic feed library, "
                "per-ingredient A/B/C fractions and Kd)",
        equation_number="No single equation number -- a chained kinetic system; "
                         "see this module's docstring for the scope decision",
    )

    variables = [
        Variable(symbol="user_diet", name="Ration (ingredient names + kg DM/d)", unit="n/a"),
        Variable(symbol="animal_input", name="Full animal state (needed for the microbial-half full model run)", unit="n/a"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake (passed through, not re-predicted)", unit="kg/d"),
    ]

    formula_text = "An_MPIn (kg/d) = Du_idMiTP_g/1000 + Dt_idRUPIn  (microbial + RUP contributions)"

    assumptions = [
        "DMI is passed through from the caller (DMIn_eqn=0 for the "
        "full-model microbial path; dmi_kg directly for the independent "
        "RUP path), not re-predicted -- keeps this consistent with "
        "whichever DMI equation (Eq. 2-1 or 2-2) produced the DMI value "
        "used elsewhere in a given report.",
        "Milk protein/fat prediction equation selection (mPrt_eqn, "
        "mFat_eqn) uses the reference software's own defaults for the "
        "full-model run that still supplies the microbial half, since "
        "these affect predicted milk composition outputs, not the "
        "microbial supply chain this equation is used for -- not "
        "independently verified as the 'best' choice for that purpose.",
        "Gestation, growth (frame gain), and body reserve gain default to "
        "zero/non-pregnant unless explicitly set on the AnimalState -- "
        "the microbial supply number (still full-model-derived) is not "
        "sensitive to these in the same way requirement-side numbers "
        "would be, but this has not been independently confirmed for "
        "every field. The RUP number is unaffected, since it no longer "
        "goes through the full model at all.",
    ]

    applicability = (
        "Any lactating dairy cow with a defined ration built from real feed "
        "library ingredients (via feed_library.ration.Ration) and a "
        "complete AnimalState."
    )

    limitations = [
        "The microbial half still wraps the full model rather than "
        "independently-cited equations, so a discrepancy in THAT half "
        "cannot be traced to one specific formula the way every other "
        "equation in this codebase can. The RUP half no longer has this "
        "limitation -- it is traceable to feed_library.rup_supply's own "
        "two real nasem_dairy function calls, and gives a per-feed "
        "breakdown (RUPSupplyResult.fd_idrupin_kg) for debugging.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "RUP-derived MP supply is now sourced independently via "
        "feed_library.rup_supply.compute_rup_supply(), not from a full "
        "model run. Verified to match the full model's own Dt_idRUPIn to "
        "rel_tol=1e-6 on the real lactating_cow_test demo scenario "
        "(tests/test_rup_supply.py) before being wired in here.",
        "Microbial-derived MP supply (Du_idMiTP_g) still requires a full "
        "nasem_dairy.nasem() model run. This is NOT the same gap as "
        "before -- MicrobialMPSupplyNASEM2021 itself is already an "
        "independently-cited equation, but its own required inputs "
        "(Rum_DigNDFIn, Rum_DigStIn, An_RDPIn) are not yet independently "
        "mapped in this codebase (see MicrobialCrudeProteinNASEM2021's "
        "own known_discrepancies). Mapping those is the natural way to "
        "close this remaining half -- tracked here as future work, not "
        "silently accepted as sufficient.",
    ]

    def calculate(
        self,
        animal: AnimalState,
        milk: MilkTarget,
        ration: Ration,
        dmi_kg: float,
        model_output=None,
    ) -> EquationResult:
        """
        RUP-derived MP supply is computed independently via
        feed_library.rup_supply.compute_rup_supply() -- no full model run
        needed for this half.

        Microbial-derived MP supply (Du_idMiTP_g) still requires a full
        model run. If model_output is provided (a ModelOutput from a
        prior run_full_model() call, e.g. one already run by
        RequirementsReport for the same animal/milk/ration/dmi), it is
        reused instead of running the full model again -- avoids running
        nd.nasem() twice for the same scenario.
        """
        rup_result = compute_rup_supply(ration=ration, dmi_kg=dmi_kg)
        dt_idrupin_kg = rup_result.dt_idrupin_kg

        if model_output is None:
            from anllms.simulation.nasem_model_bridge import run_full_model

            model_output = run_full_model(animal, milk, ration, dmi_kg)

        du_idmitp_g = model_output.get_value("Du_idMiTP_g")
        total_mp_supply_g = du_idmitp_g + (dt_idrupin_kg * 1000)

        return EquationResult(
            value=total_mp_supply_g,
            unit="g/d",
            inputs_used={
                "DMI (kg/d, passed through)": dmi_kg,
                "Microbial MP supply (g/d, Du_idMiTP_g, from full model run)": du_idmitp_g,
                "RUP-derived MP supply (g/d, independently computed via "
                "feed_library.rup_supply, x1000)": dt_idrupin_kg * 1000,
                "Per-feed RUP-derived MP supply (g/d)": {
                    name: kg * 1000 for name, kg in rup_result.fd_idrupin_kg.items()
                },
                "Ration": list(zip(ration.feedstuffs, ration.kg_dm_per_day)),
            },
            equation=self,
        )
