"""
Total metabolizable protein (MP) supply from the diet — microbial + RUP.

SCOPE DECISION, stated explicitly rather than hidden: every other equation
in this codebase wraps ONE (or a small handful of) specific, citable
nasem_dairy function(s). RUP-derived MP supply cannot practically be
wrapped that way -- it depends on a chain of 100+ functions implementing
rumen escape kinetics (per-ingredient A/B/C protein fractions, degradation
rate Kd, passage rate Kp, first-order kinetic integration) that are
tightly coupled to the rest of the model (DMI, rumen digestion of NDF/
starch, etc.). Reproducing that chain function-by-function as separate
knowledge objects, the way MP maintenance's four sub-equations were done,
would be disproportionate scope for the value gained right now.

INSTEAD, this equation wraps a full nasem_dairy.nasem() model run and
extracts the total MP supply outputs (Dt_idRUPIn for RUP-derived supply,
Du_idMiTP_g for microbial-derived supply, matching
MicrobialMPSupplyNASEM2021's own equation -- both should agree when given
consistent inputs, which is checked in this codebase's tests).

Book citation for the underlying RUP kinetics: NASEM (2021) Chapter 6
("Ruminal Protein Degradation" / RDP-RUP discussion) and Chapter 19 (the
electronic feed library providing per-ingredient A/B/C fractions and
Kd). No single equation number covers the full chain -- it is a kinetic
system built from many equations together (see Chapter 6 narrative
description of the first-order A/B/C/Kd/Kp model), not one formula.

WHAT THIS TAKES AS INPUT: a full AnimalState (including the
previously-optional gestation/breed/environment fields, now required
here since the full model needs them) and a Ration built from real feed
library ingredients. DMI is NOT re-predicted by this equation -- the
caller's own DMI value is passed through directly (DMIn_eqn=0), so this
stays consistent with whichever DMI equation (Eq. 2-1 or 2-2) the rest of
the report used, rather than letting the full model compute its own
independent DMI.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE
from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget


class TotalMPSupplyNASEM2021(KnowledgeEquation):
    """Total MP supply from the diet: microbial + RUP (NASEM 2021, full model run)."""

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
        Variable(symbol="animal_input", name="Full animal state", unit="n/a"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake (passed through, not re-predicted)", unit="kg/d"),
    ]

    formula_text = "An_MPIn (kg/d) = Du_idMiTP_g/1000 + Dt_idRUPIn  (microbial + RUP contributions)"

    assumptions = [
        "DMI is passed through from the caller (DMIn_eqn=0), not "
        "re-predicted by the full model -- keeps this consistent with "
        "whichever DMI equation (Eq. 2-1 or 2-2) produced the DMI value "
        "used elsewhere in a given report.",
        "Milk protein/fat prediction equation selection (mPrt_eqn, "
        "mFat_eqn) uses the reference software's own defaults, since "
        "these affect predicted milk composition outputs, not the RUP/"
        "microbial supply chain this equation is used for -- not "
        "independently verified as the 'best' choice for that purpose.",
        "Gestation, growth (frame gain), and body reserve gain default to "
        "zero/non-pregnant unless explicitly set on the AnimalState -- "
        "supply-side numbers (RUP, microbial protein) are not sensitive "
        "to these in the same way requirement-side numbers would be, but "
        "this has not been independently confirmed for every field.",
    ]

    applicability = (
        "Any lactating dairy cow with a defined ration built from real feed "
        "library ingredients (via feed_library.ration.Ration) and a "
        "complete AnimalState."
    )

    limitations = [
        "Because this wraps the full model rather than individual cited "
        "equations, a discrepancy here cannot be traced to one specific "
        "formula the way every other equation in this codebase can -- "
        "debugging an unexpected value requires either trusting the "
        "reference software's internals or doing the equation-by-equation "
        "mapping work this scope decision deferred.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "This equation has NOT been decomposed into individually-cited "
        "sub-equations the way MP maintenance (4 parts) or milk MP "
        "requirement was. Doing so is the natural way to close this gap "
        "properly -- tracked here as future work, not silently accepted "
        "as sufficient.",
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
        If model_output is provided (a ModelOutput from a prior
        run_full_model() call, e.g. one already run by RequirementsReport
        for the same animal/milk/ration/dmi), it is reused instead of
        running the full model again -- avoids running nd.nasem() twice
        for the same scenario.
        """
        if model_output is None:
            from anllms.simulation.nasem_model_bridge import run_full_model

            model_output = run_full_model(animal, milk, ration, dmi_kg)

        du_idmitp_g = model_output.get_value("Du_idMiTP_g")
        dt_idrupin_kg = model_output.get_value("Dt_idRUPIn")
        total_mp_supply_g = du_idmitp_g + (dt_idrupin_kg * 1000)

        return EquationResult(
            value=total_mp_supply_g,
            unit="g/d",
            inputs_used={
                "DMI (kg/d, passed through)": dmi_kg,
                "Microbial MP supply (g/d, Du_idMiTP_g)": du_idmitp_g,
                "RUP-derived MP supply (g/d, Dt_idRUPIn x1000)": dt_idrupin_kg * 1000,
                "Ration": list(zip(ration.feedstuffs, ration.kg_dm_per_day)),
            },
            equation=self,
        )
