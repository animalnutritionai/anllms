"""
Ingredient lookup — wraps the REAL NASEM (2021) feed library shipped with
the animalnutritionai/NASEM-Model-Python fork, via nasem_dairy.select_feeds().

This REPLACES an earlier placeholder version of this file that invented
its own Ingredient schema from first principles. That was a mistake this
codebase's own methodology should have caught immediately: check the
reference source before designing a data shape, not after. The real feed
library already contains 284 ingredients with the actual NASEM rumen
degradability kinetics data (A/B/C protein fractions, degradation rate,
RUP intestinal digestibility), full amino acid profiles, and mineral/
vitamin content -- this file wraps that directly rather than
reimplementing any of it.

Source: NASEM (2021) Chapter 19's feed composition table / "electronic
feed library" (the book's own term -- see Chapter 6 narrative, which notes
the electronic library has stronger per-feed data than the printed table).
Shipped as src/nasem_dairy/data/feed_library/NASEM_feed_library.csv in the
animalnutritionai/NASEM-Model-Python fork.

CAVEAT (worth stating plainly, same pattern as software_reference
elsewhere in this codebase): the book distinguishes the printed feed
table from the "electronic feed library," and a maintained GitHub fork
could add, remove, or revise entries over time independent of the printed
2021 edition. Treat ingredient values as sourced from the fork's current
CSV snapshot, not as frozen to the original 2021 print edition, unless
independently checked.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Ingredient:
    """
    A single feed ingredient's data, pulled directly from the real NASEM
    feed library (not reconstructed or guessed). Field names deliberately
    mirror the library's own column names (Fd_ prefix) so they stay
    traceable back to the source table rather than being renamed into a
    scheme this codebase invented.
    """

    name: str
    dm_pct: float                    # Fd_DM, % as-fed
    cp_pct: float                    # Fd_CP, % of DM
    ndf_pct: float                   # Fd_NDF, % of DM
    adf_pct: float                   # Fd_ADF, % of DM
    starch_pct: float | None         # Fd_St
    fat_pct: float | None            # Fd_CFat
    ash_pct: float | None            # Fd_Ash
    is_forage: bool                  # derived from Fd_Conc == 0 (Fd_Conc: 100=concentrate, 0=forage)

    # Real rumen degradability kinetics (NASEM A/B/C fraction system,
    # per Chapter 6: A = rapidly washed-out fraction, B = potentially
    # degradable at rate Kd, C = indigestible fraction).
    cp_a_fraction_pct: float | None  # Fd_CPARU, % of CP
    cp_b_fraction_pct: float | None  # Fd_CPBRU, % of CP
    cp_c_fraction_pct: float | None  # Fd_CPCRU, % of CP
    kd_rup_per_hour: float | None    # Fd_KdRUP, degradation rate of B fraction
    rup_intestinal_digestibility_pct: float | None  # Fd_dcRUP

    forage_ndf_digestibility_48h_pct: float | None  # Fd_DNDF48_NDF, only meaningful if is_forage

    source_note: str = (
        "NASEM (2021) Chapter 19 electronic feed library, via "
        "animalnutritionai/NASEM-Model-Python NASEM_feed_library.csv"
    )

    @classmethod
    def from_library(cls, name: str) -> "Ingredient":
        """Look up one ingredient by exact name from the real feed library."""
        import nasem_dairy as nd

        rows = nd.select_feeds([name])
        if len(rows) == 0:
            raise ValueError(
                f"Ingredient '{name}' not found in the NASEM feed library. "
                f"Names must match exactly (case- and punctuation-sensitive); "
                f"consider searching the library directly if unsure of the "
                f"exact name."
            )
        row = rows.iloc[0]

        def _get(col):
            val = row.get(col)
            if val is None or (isinstance(val, float) and val != val):  # NaN check
                return None
            return float(val)

        return cls(
            name=str(row["Fd_Name"]),
            dm_pct=float(row["Fd_DM"]),
            cp_pct=float(row["Fd_CP"]),
            ndf_pct=float(row["Fd_NDF"]),
            adf_pct=float(row["Fd_ADF"]),
            starch_pct=_get("Fd_St"),
            fat_pct=_get("Fd_CFat"),
            ash_pct=_get("Fd_Ash"),
            is_forage=(float(row.get("Fd_Conc", 100)) == 0),
            cp_a_fraction_pct=_get("Fd_CPARU"),
            cp_b_fraction_pct=_get("Fd_CPBRU"),
            cp_c_fraction_pct=_get("Fd_CPCRU"),
            kd_rup_per_hour=_get("Fd_KdRUP"),
            rup_intestinal_digestibility_pct=_get("Fd_dcRUP"),
            forage_ndf_digestibility_48h_pct=_get("Fd_DNDF48_NDF"),
        )


def search_feed_library(query: str, limit: int = 20) -> list[str]:
    """
    Case-insensitive substring search over real ingredient names in the
    feed library -- useful since Ingredient.from_library() requires an
    exact name match. Returns matching Fd_Name values.
    """
    import importlib.resources as resources

    import pandas as pd

    try:
        csv_path = resources.files("nasem_dairy.data.feed_library").joinpath(
            "NASEM_feed_library.csv"
        )
        full_library = pd.read_csv(csv_path)
    except Exception as e:
        raise RuntimeError(
            f"Could not load the bundled feed library CSV for searching: {e}"
        )

    matches = full_library[
        full_library["Fd_Name"].str.contains(query, case=False, na=False)
    ]["Fd_Name"].tolist()
    return matches[:limit]
