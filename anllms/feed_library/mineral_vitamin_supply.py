"""
Independent mineral/vitamin supply -- closes the last "extracted from a
shared full-model run" gap in supply-side calculations (see each
scientific/minerals/*.py and scientific/vitamins/*.py known_discrepancies,
and docs/architecture.md's "Mineral/vitamin supply equations" open item).

Same pattern as rup_supply.py and microbial_substrate.py: uses the real
nasem_dairy per-feed nutrient-intake pipeline via _feed_data.py's
build_complete_feed_data() -- NOT a full nd.nasem() run -- then calls the
real nasem_dairy summing functions on the per-feed columns that pipeline
already produces. No science reimplemented: every summation and the
magnesium absorption-coefficient chain (Dt_acMg, which depends on
dietary K%) call the real nasem_dairy functions directly.

Two supply patterns, both confirmed against nasem_dairy's own
nutrient_intakes.py source (calculate_feed_data() and calculate_diet_data()):

- 11 minerals have a per-feed absorption coefficient already computed as
  a Fd_abs*In column inside calculate_feed_data() (the same function
  build_complete_feed_data() calls): Ca, P, Na, K, Cl, Co, Cu, Fe, Mn, Zn
  are a direct sum of that column via the real calculate_Abs_*In()
  function. Mg is the one exception -- Dt_acMg (the diet-level absorption
  coefficient) is inhibited by dietary K%, so it needs the intermediate
  diet-level chain (Dt_MgIn, Dt_MgIn_min, Dt_KIn -> Dt_K -> Dt_acMg ->
  Abs_MgIn) rather than a simple per-feed sum.
- 3 minerals (S, I, Se) and all 3 vitamins (A, D, E) have NO absorption
  coefficient in the book at all -- supply is just the diet-total intake
  sum (Dt_SIn, Dt_IIn, Dt_SeIn, Dt_VitAIn, Dt_VitDIn, Dt_VitEIn), already
  confirmed by the absence of any Fd_ac* function for these six.
"""

from __future__ import annotations

from anllms.feed_library._feed_data import build_complete_feed_data
from anllms.feed_library.ration import Ration

# nasem_dairy variable name -> per-feed column it is a direct sum of.
_DIRECT_SUM_KEYS = {
    # 10 minerals with a per-feed absorption coefficient (Mg handled separately).
    "Abs_CaIn": "Fd_absCaIn",
    "Abs_PIn": "Fd_absPIn",
    "Abs_NaIn": "Fd_absNaIn",
    "Abs_KIn": "Fd_absKIn",
    "Abs_ClIn": "Fd_absClIn",
    "Abs_CoIn": "Fd_absCoIn",
    "Abs_CuIn": "Fd_absCuIn",
    "Abs_FeIn": "Fd_absFeIn",
    "Abs_MnIn": "Fd_absMnIn",
    "Abs_ZnIn": "Fd_absZnIn",
    # 3 minerals + 3 vitamins with no absorption coefficient at all.
    "Dt_SIn": "Fd_SIn",
    "Dt_IIn": "Fd_IIn",
    "Dt_SeIn": "Fd_SeIn",
    "Dt_VitAIn": "Fd_VitAIn",
    "Dt_VitDIn": "Fd_VitDIn",
    "Dt_VitEIn": "Fd_VitEIn",
}

# Maps each key above to the real nasem_dairy function name that sums it
# (all are a plain pandas .sum(), but we call the real function rather
# than reimplementing .sum() ourselves, per this project's wrap-don't-
# reimplement rule).
_DIRECT_SUM_FUNCS = {
    "Abs_CaIn": "calculate_Abs_CaIn",
    "Abs_PIn": "calculate_Abs_PIn",
    "Abs_NaIn": "calculate_Abs_NaIn",
    "Abs_KIn": "calculate_Abs_KIn",
    "Abs_ClIn": "calculate_Abs_ClIn",
    "Abs_CoIn": "calculate_Abs_CoIn",
    "Abs_CuIn": "calculate_Abs_CuIn",
    "Abs_FeIn": "calculate_Abs_FeIn",
    "Abs_MnIn": "calculate_Abs_MnIn",
    "Abs_ZnIn": "calculate_Abs_ZnIn",
    "Dt_SIn": "calculate_Dt_SIn",
    "Dt_IIn": "calculate_Dt_IIn",
    "Dt_SeIn": "calculate_Dt_SeIn",
    "Dt_VitAIn": "calculate_Dt_VitAIn",
    "Dt_VitDIn": "calculate_Dt_VitDIn",
    "Dt_VitEIn": "calculate_Dt_VitEIn",
}


def compute_mineral_vitamin_supply(
    ration: Ration,
    dmi_kg: float,
    an_state_phys: str = "Lactating Cow",
) -> dict[str, float]:
    """
    Independently computes all 14 mineral + 3 vitamin diet supply values
    from the real per-feed nasem_dairy pipeline -- the same
    complete_feed_data DataFrame RUP/microbial supply already use -- with
    no full nd.nasem() model run required.

    Returns a flat dict keyed by the nasem_dairy variable name (Abs_CaIn,
    Dt_SIn, Dt_VitAIn, ...) so each *SupplyNASEM2021.calculate() can look
    up its own value the same way model_output.get_value(...) used to.
    """
    import nasem_dairy as nd

    feed_data = build_complete_feed_data(ration, dmi_kg, an_state_phys=an_state_phys)

    supply: dict[str, float] = {}
    for result_key, column in _DIRECT_SUM_KEYS.items():
        func = getattr(nd, _DIRECT_SUM_FUNCS[result_key])
        supply[result_key] = func(feed_data[column])

    # Magnesium: Dt_acMg (diet-level absorption coefficient) is inhibited
    # by dietary K%, so Abs_MgIn is NOT a simple per-feed sum -- it needs
    # this intermediate diet-level chain. Every step below is a real
    # nasem_dairy function, matching nutrient_intakes.py's own
    # calculate_diet_data() call sequence exactly.
    dt_mg_in = nd.calculate_Dt_MgIn(feed_data["Fd_MgIn"])
    dt_mg_in_min = nd.calculate_Dt_MgIn_min(feed_data["Fd_MgIn_min"])
    dt_k_in = nd.calculate_Dt_KIn(feed_data["Fd_KIn"])
    dt_k = nd.calculate_Dt_K(dt_k_in, dmi_kg)
    dt_ac_mg = nd.calculate_Dt_acMg(an_state_phys, dt_k, dt_mg_in_min, dt_mg_in)
    supply["Abs_MgIn"] = nd.calculate_Abs_MgIn(dt_ac_mg, dt_mg_in)

    return supply
