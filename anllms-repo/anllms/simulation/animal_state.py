"""
Simulation Layer — core data model.

These dataclasses hold the animal-, production-, and diet-level inputs
that get threaded through the Scientific Layer's knowledge-object
equations. They are plain data containers with NO calculation logic of
their own — all calculation stays inside the equation knowledge objects,
per project architecture.

SCOPE NOTE on Diet: several fields (forage_ndf_digestibility_pct, etc.)
are still entered as single diet-level values rather than derived from a
Ration's actual ingredient composition -- see feed_library.ration.Ration,
which handles MP SUPPLY (the piece that most needed real ingredient data)
separately via TotalMPSupplyNASEM2021. Diet still covers DMI/MP-
maintenance equations' needs directly for now.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnimalState:
    """Animal-side inputs shared across most requirement equations."""

    bw_kg: float
    bcs: float                 # NASEM 1-5 scale
    days_in_milk: int
    parity: int                # 1 = primiparous, 2+ = multiparous; 0 reserved for non-lactating/growing animals

    # --- Optional fields, only needed for a FULL nasem_dairy model run
    # (e.g. to get RUP-derived MP supply via TotalMPSupplyNASEM2021).
    # Defaults represent a non-pregnant, mature Holstein cow in a standard
    # confinement/parlor setup -- NOT computed or validated by this
    # codebase, just passed through to the reference software. Override
    # any of these that matter for a specific animal/scenario.
    bw_mature_kg: float | None = None       # An_BW_mature; defaults to bw_kg if unset
    gestation_day: int = 0                  # An_GestDay; 0 = not pregnant
    gestation_length_day: int = 280         # An_GestLength
    calf_birth_weight_kg: float = 44.1      # Fet_BWbrth (only matters if gestation_day > 0)
    age_day: int | None = None              # An_AgeDay; if unset, a placeholder mature age is used
    breed: str = "Holstein"                 # An_Breed
    age_at_dry_feed_start_day: int = 14     # An_AgeDryFdStart (calf-rearing param; irrelevant for adult cows)
    frame_gain_kg_per_day: float = 0.0      # Trg_FrmGain; 0 = no targeted frame growth
    reserve_gain_kg_per_day: float = 0.0    # Trg_RsrvGain; 0 = no targeted body reserve change
    env_temp_c: float = 22.0                # Env_TempCurr; thermoneutral default
    env_distance_to_parlor_m: float = 0.0   # Env_DistParlor
    env_trips_to_parlor: int = 0            # Env_TripsParlor
    env_topography_code: int = 0            # Env_Topo

    def to_animal_input_dict(self, milk: "MilkTarget", dmi_kg: float) -> dict:
        """
        Build the raw animal_input dict nasem_dairy expects, then validate
        it through the REAL nasem_dairy.model.input_validation.validate_animal_input()
        -- we do not trust our own dataclass as validated; theirs is the
        source of truth for required keys, types, and coercion.
        """
        from nasem_dairy.model.input_validation import validate_animal_input

        raw = {
            "An_Parity_rl": self.parity,
            "Trg_MilkProd": milk.yield_kg,
            "An_BW": self.bw_kg,
            "An_BCS": self.bcs,
            "An_LactDay": self.days_in_milk,
            "Trg_MilkFatp": milk.fat_pct,
            "Trg_MilkTPp": milk.true_protein_pct,
            "Trg_MilkLacp": milk.lactose_pct,
            "Trg_Dt_DMIn": dmi_kg,
            "An_BW_mature": self.bw_mature_kg or self.bw_kg,
            "Trg_FrmGain": self.frame_gain_kg_per_day,
            "An_GestDay": self.gestation_day,
            "An_GestLength": self.gestation_length_day,
            "Trg_RsrvGain": self.reserve_gain_kg_per_day,
            "Fet_BWbrth": self.calf_birth_weight_kg,
            "An_AgeDay": self.age_day or 1500,  # placeholder mature age if unset
            "An_305RHA_MlkTP": 280,  # reference software default; not independently verified
            "An_StatePhys": "Lactating Cow",
            "An_Breed": self.breed,
            "An_AgeDryFdStart": self.age_at_dry_feed_start_day,
            "Env_TempCurr": self.env_temp_c,
            "Env_DistParlor": self.env_distance_to_parlor_m,
            "Env_TripsParlor": self.env_trips_to_parlor,
            "Env_Topo": self.env_topography_code,
        }
        return validate_animal_input(raw)


@dataclass
class MilkTarget:
    """Target or actual milk production and composition."""

    yield_kg: float
    fat_pct: float
    true_protein_pct: float | None = None
    lactose_pct: float | None = None


@dataclass
class Diet:
    """
    Diet-level inputs used by DMI and MP-maintenance equations. MP SUPPLY
    no longer uses this class -- see feed_library.ration.Ration and
    TotalMPSupplyNASEM2021, which use real feed-library ingredient data
    instead.
    """

    ndf_pct: float                          # % of DM
    adf_pct: float                          # % of DM
    forage_ndf_pct: float                   # % of DM
    forage_ndf_digestibility_pct: float     # % of forage NDF, 48h in vitro/in situ

    # Legacy fields from before the real feed library wrapper existed.
    # No longer used by build_requirements_report; kept optional for any
    # direct use of MicrobialMPSupplyNASEM2021 in isolation.
    rdp_pct: float | None = None
    rumen_digested_ndf_kg: float | None = None
    rumen_digested_starch_kg: float | None = None
