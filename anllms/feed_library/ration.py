"""
Ration — wraps the REAL diet-building and aggregation pipeline from
animalnutritionai/NASEM-Model-Python, replacing the earlier placeholder
that reimplemented DMI-weighted averaging by hand.

A Ration here is just a list of (ingredient name, kg DM/d) pairs -- the
exact shape nasem_dairy.nasem()'s `user_diet` argument expects (columns
'Feedstuff' and 'kg_user', confirmed against nd.demo() output). Diet-level
aggregate values (Dt_NDF, Dt_RDP, Dt_idRUPIn, etc.) are obtained by
calling the real model, not recomputed here -- this file does NOT contain
any weighted-average math of its own.

SCOPE NOTE: producing per-feed derived values (RUP, digestibility, etc.)
via nd.calculate_feed_data() requires An_StatePhys and Dt_DMIn as inputs,
and getting full diet-level totals (Dt_idRUPIn, the RUP-derived MP supply
this was ultimately meant to unblock) requires the full nd.nasem() call
with complete animal_input and equation_selection dictionaries. This file
provides the plumbing to build user_diet correctly; running the full
model with a complete AnimalState/MilkTarget mapping is the next step
(see docs/architecture.md), not yet wired up here.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ration:
    """A ration: ingredient names (matching the real feed library exactly) and kg DM/d."""

    feedstuffs: list[str] = field(default_factory=list)
    kg_dm_per_day: list[float] = field(default_factory=list)

    def add(self, feedstuff_name: str, kg_dm_per_day: float) -> None:
        if kg_dm_per_day < 0:
            raise ValueError("kg_dm_per_day cannot be negative")
        self.feedstuffs.append(feedstuff_name)
        self.kg_dm_per_day.append(kg_dm_per_day)

    @classmethod
    def guelph_base_diet(cls) -> "Ration":
        """
        nasem_dairy's own built-in demo ration (nd.demo("lactating_cow_test")),
        used as a fallback diet composition when a caller hasn't formulated
        one of their own. This is NOT a NASEM (2021) book example -- it is
        the reference software's own demo/test fixture (data/demo/ folder,
        package v1.0.2, matching NASEM_DAIRY_2021_SOFTWARE's pinned version).
        Cite it as such (SoftwareReference, not a book Citation) wherever
        it's surfaced to a user.

        Paired animal scenario ("Example Lactating Cow, 100 DIM"): Holstein,
        parity 1, BW 624.795 kg, BCS 3, 100 DIM, day 46 gestation, target
        25.062 kg/d milk @ 4.55% fat / 3.66% TP / 4.85% lactose. Total DMI
        in the original scenario: 24.521 kg/d.
        """
        ration = cls()
        ration.add("Alfalfa meal", 8.2101564407)
        ration.add("Canola meal", 6.7323288918)
        ration.add("Corn silage, typical", 5.4734377861)
        ration.add("Corn grain HM, coarse grind", 4.1050782204)
        return ration

    @property
    def total_dmi_kg(self) -> float:
        return sum(self.kg_dm_per_day)

    def to_user_diet_df(self):
        """
        Build the exact DataFrame shape nasem_dairy.nasem() expects for
        its `user_diet` argument: columns 'Feedstuff' and 'kg_user'.
        """
        import pandas as pd

        if not self.feedstuffs:
            raise ValueError("Ration has no ingredients")

        return pd.DataFrame({"Feedstuff": self.feedstuffs, "kg_user": self.kg_dm_per_day})

    def validate_feedstuffs_exist(self) -> list[str]:
        """
        Check every ingredient name against the real feed library BEFORE
        attempting a full model run, so mistyped names fail fast with a
        clear message rather than a confusing downstream error. Returns
        the list of names that were NOT found (empty list = all valid).
        """
        import nasem_dairy as nd

        missing = []
        for name in self.feedstuffs:
            rows = nd.select_feeds([name])
            if len(rows) == 0:
                missing.append(name)
        return missing

    def to_diet(self):
        """
        Derive diet-level aggregate values (Dt_NDF, Dt_ADF, Dt_ForNDF,
        Dt_ForDNDF48_ForNDF) needed by simulation.animal_state.Diet, using
        the REAL nasem_dairy per-feed aggregation functions -- no
        hand-rolled weighted-average math here. Chain:
            Fd_DMInp -> per-feed fraction of total ration DM
            Fd_ForNDF -> per-feed forage NDF (0 for concentrates)
            Fd_DNDF48 -> per-feed absolute forage NDF digestibility contribution
            Dt_NDF, Dt_ADF, Dt_ForNDF, Dt_ForDNDF48 -> weighted sums (their functions)
            Dt_ForDNDF48_ForNDF -> Dt_ForDNDF48 / Dt_ForNDF * 100 (their function)

        Uses this Ration's own total DM (not any animal's predicted DMI)
        as the basis for per-feed fractions -- diet COMPOSITION is
        intrinsic to the ration, independent of how much of it the animal
        is predicted to eat.
        """
        from anllms.simulation.animal_state import Diet
        import nasem_dairy as nd

        missing = self.validate_feedstuffs_exist()
        if missing:
            raise ValueError(
                f"Ration contains ingredient name(s) not found in the real "
                f"feed library: {missing}. Names must match exactly."
            )

        user_diet_df = self.to_user_diet_df()
        feed_library = nd.select_feeds(self.feedstuffs)
        feed_data = nd.get_feed_data(self.total_dmi_kg, user_diet_df, feed_library)

        fd_dminp = nd.calculate_Fd_DMInp(feed_data["kg_user"])
        fd_fornd = nd.calculate_Fd_ForNDF(feed_data["Fd_NDF"], feed_data["Fd_Conc"])
        fd_dndf48 = nd.calculate_Fd_DNDF48(feed_data["Fd_Conc"], feed_data["Fd_DNDF48_input"])

        dt_ndf = nd.calculate_Dt_NDF(fd_dminp, feed_data["Fd_NDF"])
        dt_adf = nd.calculate_Dt_ADF(fd_dminp, feed_data["Fd_ADF"])
        dt_fornd_total = nd.calculate_Dt_ForNDF(fd_dminp, fd_fornd)
        dt_fordndf48 = nd.calculate_Dt_ForDNDF48(
            fd_dminp, feed_data["Fd_Conc"], feed_data["Fd_NDF"], fd_dndf48
        )
        dt_fordndf48_fornd = nd.calculate_Dt_ForDNDF48_ForNDF(dt_fordndf48, dt_fornd_total)

        return Diet(
            ndf_pct=dt_ndf,
            adf_pct=dt_adf,
            forage_ndf_pct=dt_fornd_total,
            forage_ndf_digestibility_pct=dt_fordndf48_fornd or 0.0,
        )
