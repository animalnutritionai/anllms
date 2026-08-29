"""
RUP-derived digestible protein supply — wraps the REAL nasem_dairy
per-feed nutrient-intake pipeline, replacing the earlier approach (in
scientific/protein/total_mp_supply.py) of running the FULL nd.nasem()
model just to extract this one number.

WHY THIS IS POSSIBLE WITHOUT REPRODUCING 100+ FUNCTIONS BY HAND:
nasem_dairy already packages its entire rumen-escape kinetics chain
(A/B/C protein fractions, degradation rate Kd, passage rate Kp,
first-order kinetic integration) into ONE reusable wrapper function,
nd.calculate_feed_data() -- the exact same function the real model
calls internally (see nasem_equations/nutrient_intakes.py's
calculate_feed_data(), called from model/nasem.py). Given per-feed
library data, diet DMI, animal physiological state, and the standard
coefficient dictionary, it returns every per-feed column in the RUP
chain, including Fd_idRUPIn (intestinally digestible RUP per feed).
A second real function, nd.calculate_Dt_idRUPIn(), sums that to the
diet total. This module calls both directly -- no math from either
function is reimplemented here.

This does NOT run the full nd.nasem() model (no milk protein/fat
prediction, no maintenance/gestation/growth requirement calculations
are touched) -- only the subset of the pipeline needed to get from a
Ration to per-feed and diet-total digestible RUP.

Book citation for the underlying kinetics: NASEM (2021) Chapter 6
("Ruminal Protein Degradation" / RDP-RUP discussion) and Chapter 19
(electronic feed library providing per-ingredient A/B/C fractions and
Kd). As with total_mp_supply.py, no single equation number covers this
whole chain -- it is a kinetic system built from many equations
together, not one formula. This module is data-layer plumbing (like
ration.py), not a citable single-formula KnowledgeEquation in its own
right -- callers that need a citation-bearing equation object should
build on TOTAL MP supply's KnowledgeEquation subclass, not this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from anllms.feed_library.ration import Ration


@dataclass
class RUPSupplyResult:
    """Diet-level and per-feed digestible RUP supply."""

    dt_idrupin_kg: float                       # Dt_idRUPIn, kg/d, diet total
    fd_idrupin_kg: dict[str, float]             # per-feed Fd_idRUPIn, kg/d, keyed by feedstuff name

    # Also surfaced for transparency / debugging, since they're
    # intermediate values in the same real chain:
    dt_rupin_kg: float                          # Dt_RUPIn, kg/d, diet total RUP intake (pre-digestion)
    fd_rupin_kg: dict[str, float]                # per-feed Fd_RUPIn, kg/d


def compute_rup_supply(
    ration: Ration,
    dmi_kg: float,
    an_state_phys: str = "Lactating Cow",
    use_dndf_iv: int = 0,
) -> RUPSupplyResult:
    """
    Computes digestible (intestinally absorbable) RUP supply for a
    Ration, using the real nasem_dairy per-feed nutrient-intake pipeline
    directly -- no full nd.nasem() model run.

    dmi_kg: the diet's actual dry matter intake (kg/d). Callers should
    pass the same DMI value used elsewhere in a given report (matching
    total_mp_supply.py's DMIn_eqn=0 convention -- this is NOT
    re-predicted here).

    an_state_phys: matches nasem_dairy's An_StatePhys input. This
    codebase currently only models lactating cows (see
    simulation/animal_state.py), so "Lactating Cow" is the only value
    exercised/validated so far.

    use_dndf_iv: matches nasem_dairy's Use_DNDF_IV equation_selection
    flag. Defaults to 0, matching this codebase's existing convention
    in simulation/nasem_model_bridge.py's run_full_model().
    """
    missing = ration.validate_feedstuffs_exist()
    if missing:
        raise ValueError(
            f"Ration contains ingredient name(s) not found in the real "
            f"feed library: {missing}. Names must match exactly."
        )
    if dmi_kg <= 0:
        raise ValueError("dmi_kg must be positive")

    import nasem_dairy as nd

    user_diet_df = ration.to_user_diet_df()
    feed_library = nd.select_feeds(ration.feedstuffs)
    feed_data = nd.get_feed_data(dmi_kg, user_diet_df, feed_library)
    feed_data["Fd_ForNDF"] = nd.calculate_Fd_ForNDF(
        feed_data["Fd_NDF"], feed_data["Fd_Conc"]
    )

    complete_feed_data = nd.calculate_feed_data(
        dmi_kg, an_state_phys, use_dndf_iv, feed_data, nd.coeff_dict
    )

    dt_idrupin_kg = nd.calculate_Dt_idRUPIn(complete_feed_data["Fd_idRUPIn"])
    dt_rupin_kg = nd.calculate_Dt_RUPIn(complete_feed_data["Fd_RUPIn"])

    return RUPSupplyResult(
        dt_idrupin_kg=float(dt_idrupin_kg),
        fd_idrupin_kg=dict(
            zip(ration.feedstuffs, complete_feed_data["Fd_idRUPIn"].tolist())
        ),
        dt_rupin_kg=float(dt_rupin_kg),
        fd_rupin_kg=dict(
            zip(ration.feedstuffs, complete_feed_data["Fd_RUPIn"].tolist())
        ),
    )
