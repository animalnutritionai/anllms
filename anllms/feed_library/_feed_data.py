"""
Internal helper: builds the real nasem_dairy per-feed `complete_feed_data`
DataFrame from a Ration -- the shared first step used by BOTH
rup_supply.py and microbial_substrate.py, factored out here so that
shared setup (nd.get_feed_data() -> nd.calculate_feed_data()) is called
in exactly one place rather than duplicated.

Not a citable KnowledgeEquation in its own right (same status as
rup_supply.py itself) -- this is data-layer plumbing. Callers needing a
citation-bearing equation object should build on the KnowledgeEquation
subclasses in scientific/protein/, not this module directly.

Leading underscore: internal to feed_library, not part of the public
package surface.
"""

from __future__ import annotations

from anllms.feed_library.ration import Ration


def build_complete_feed_data(
    ration: Ration,
    dmi_kg: float,
    an_state_phys: str = "Lactating Cow",
    use_dndf_iv: int = 0,
):
    """
    Validates the Ration against the real feed library, then runs the
    real nasem_dairy per-feed nutrient-intake pipeline
    (nd.get_feed_data() -> nd.calculate_feed_data()) -- the same
    functions the full model calls internally -- WITHOUT running the
    full nd.nasem() model.

    Returns the real nasem_dairy `complete_feed_data` DataFrame (one row
    per feedstuff, in ration.feedstuffs order), containing every
    per-feed column that pipeline produces -- RUP-chain columns
    (Fd_RUPIn, Fd_idRUPIn, ...), CP/RDP-chain columns (Fd_CPIn, Fd_RDP,
    Fd_RDPIn, ...), and intake-sum inputs used by the rumen-digestion
    regressions (Fd_NDFIn, Fd_StIn, Fd_ADFIn, Fd_ForWetIn, ...).

    Raises ValueError for unknown ingredient names or non-positive DMI,
    same validation rup_supply.compute_rup_supply() already performed.
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

    return nd.calculate_feed_data(
        dmi_kg, an_state_phys, use_dndf_iv, feed_data, nd.coeff_dict
    )
