"""
Canonical publication registry.

Each Publication here is a source the platform is allowed to cite.
Adding a new source model (NASEM Beef, CNCPS, INRA, etc.) starts by
registering it here with full bibliographic detail — never by inlining
a citation string somewhere in equation code.
"""

from anllms.knowledge.models import Publication, SoftwareReference

NASEM_DAIRY_2021 = Publication(
    short_name="NASEM Dairy 2021",
    full_title="Nutrient Requirements of Dairy Cattle: Eighth Revised Edition",
    authors=(
        "National Academies of Sciences, Engineering, and Medicine; "
        "Division on Earth and Life Studies; Board on Agriculture and "
        "Natural Resources; Committee on Nutrient Requirements of Dairy Cattle"
    ),
    year=2021,
    publisher="National Academies Press (US)",
    edition="8th Revised Edition",
    url="https://www.ncbi.nlm.nih.gov/books/NBK600598/",
)

NRC_DAIRY_2001 = Publication(
    short_name="NRC Dairy 2001",
    full_title="Nutrient Requirements of Dairy Cattle",
    authors="National Research Council",
    year=2001,
    publisher="National Academy Press",
    edition="7th Revised Edition",
    url=None,
)

# --- Reference software implementations (mapping/cross-validation only) ---
# See SoftwareReference docstring in knowledge/models.py for the role
# boundary: these are NEVER called at runtime by this platform.

NASEM_DAIRY_2021_SOFTWARE = SoftwareReference(
    name="nasem_dairy (NASEM-Model-Python)",
    repository_url="https://github.com/CNM-University-of-Guelph/NASEM-Model-Python",
    version_used_for_mapping="1.0.2",
    license="MIT (package code); underlying NASEM equations copied from R code "
            "distributed under separate NASEM software license terms",
    notes=(
        "Python port of the R code distributed with the official NASEM Dairy 8 "
        "software (developed by Fieguth, Innes, and Cant, University of Guelph). "
        "Per the companion 'Learning from the narrative and model in NASEM (2021)' "
        "interactive textbook (Hanigan et al., Virginia Tech), the software/R code "
        "is continually updated and is stated by NASEM's own software help "
        "documentation to contain 'the most correct and up-to-date version of the "
        "NASEM model,' whereas the printed book (NASEM_DAIRY_2021 above) is static. "
        "Used here strictly to map/verify our knowledge-object equations against "
        "the current reference implementation and to detect book-vs-software drift."
    ),
)

NASEM_BEEF_2016 = Publication(
    short_name="NASEM Beef 2016",
    full_title="Nutrient Requirements of Beef Cattle",
    authors="National Academies of Sciences, Engineering, and Medicine",
    year=2016,
    publisher="The National Academies Press",
    edition="8th Revised Edition",
    url=None,
)
