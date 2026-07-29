"""
Bridge to the real nasem_dairy.nasem() full model run.

This is NOT a reimplementation of anything in the reference repo -- it's
the one place in this codebase that assembles AnimalState + MilkTarget +
Ration into their expected input shapes (via AnimalState.to_animal_input_dict(),
which itself delegates validation to their real validate_animal_input())
and calls their real nd.nasem(). Consolidated here so equations that need
a full model run (currently just TotalMPSupplyNASEM2021, and
RequirementsReport for official requirement totals) share ONE run instead
of each building the input dict and calling nd.nasem() independently.
"""

from __future__ import annotations

from anllms.feed_library.ration import Ration
from anllms.simulation.animal_state import AnimalState, MilkTarget


def run_full_model(animal: AnimalState, milk: MilkTarget, ration: Ration, dmi_kg: float):
    """
    Runs the real nasem_dairy.nasem() model and returns its ModelOutput.
    Raises a clear error if any ration ingredient isn't in the real feed
    library, before attempting the run.
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

    animal_input = animal.to_animal_input_dict(milk, dmi_kg)
    user_diet_df = ration.to_user_diet_df()

    equation_selection = {
        "Use_DNDF_IV": 0,
        "DMIn_eqn": 0,   # use Trg_Dt_DMIn directly -- do not re-predict DMI
        "mProd_eqn": 0,
        "MiN_eqn": 1,
        "NonMilkCP_ClfLiq": 0,
        "Monensin_eqn": 0,
        "mPrt_eqn": 0,
        "mFat_eqn": 1,
        "RumDevDisc_Clf": 0,
    }

    return nd.nasem(user_diet_df, animal_input, equation_selection)
