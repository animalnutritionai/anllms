# ANLLMS Architecture Sketch — where we are, where the Feed Library goes

## Current shape (proven by simulation/requirements_report.py)

```
knowledge/          <- KnowledgeEquation base class, Publication/SoftwareReference
                        registries. No science here, just the schema.

scientific/          <- One file per equation (or tight family of equations),
  energy/               each a KnowledgeEquation subclass that WRAPS the real
  protein/              nasem_dairy function (never reimplements it), adds
                        citation/assumptions/limitations/known_discrepancies,
                        and returns an EquationResult.

simulation/           <- AnimalState / MilkTarget / Diet: plain data, no logic.
                        requirements_report.py composes equation results into
                        one explainable report. This is the layer that proves
                        equations from different files/nutrients fit together.
```

12 equations mapped so far: energy (maintenance, lactation, 2x DMI) and
protein (milk MP requirement, MP maintenance x4 sub-parts, microbial MP
supply x2). 43 unit tests + 8 integration tests, all passing, all
validated against real fixture data from the animalnutritionai fork
(not invented numbers).

## What the integration test caught

Nothing broke on the first real composition — which is itself informative:
it means the equation-by-equation interfaces (units, argument names, what
each `calculate()` needs vs. produces) were consistent enough to click
together. The one substantive thing the composed report surfaces that no
single equation could: a lactating cow's MP requirement is NOT met by
microbial protein alone (see the report's negative "partial MP balance").
That's not a bug — it's the expected, correct signal that RUP is a real
and necessary MP source, not an optional refinement.

## The Feed Library gap

Every diet-level input used so far (`Diet.ndf_pct`, `Diet.rdp_pct`,
`Diet.rumen_digested_ndf_kg`, etc.) is a single number describing "the
diet" as a whole. Real diets are built from ingredients (corn silage,
soybean meal, etc.), each with its own composition, rumen degradability,
and intestinal digestibility. A Feed Library is what turns
"18 kg corn silage + 3 kg soybean meal + ..." into the single diet-level
numbers this codebase currently requires the caller to supply directly.

### Planned shape (not yet built)

```
feed_library/
  ingredient.py       <- Ingredient knowledge object: composition (DM, CP,
                          NDF, ADF, starch, fat, ash, minerals...), rumen
                          degradability fractions (RDP/RUP split, using NASEM's
                          A/B/C fraction + kd rate-based system rather than a
                          single fixed % where possible), digestibility
                          coefficients (TTNDFD, RUP intestinal digestibility),
                          and its OWN citation (feed table source: NASEM
                          feed library, user lab analysis, or third-party
                          database) -- ingredients need provenance just like
                          equations do.
  ration.py            <- Ration = list of (Ingredient, kg DM/d). Aggregates
                          to the diet-level numbers Diet currently requires
                          directly: Dt_NDF, Dt_ADF, Dt_RDP, Dt_ForNDF, etc.,
                          via DMI-weighted averaging (per the book's own
                          guidance for fNDFD, as documented in
                          dmi_lactating_diet_aware.py's assumptions).
  rup_supply.py         <- The equation this unblocks: total digestible RUP
                          MP supply = sum over ingredients of
                          (ingredient RUP intake x ingredient intestinal RUP
                          digestibility), which is the other half of MP
                          supply alongside microbial protein.
```

### Why this wasn't built first

RUP-derived MP supply (Option A from the prior turn) requires this Feed
Library structure to be scientifically honest — a single diet-level "RUP
digestibility %" would be a simplification the project's own rules argue
against (no inventing coefficients, no simplifying published models
without approval). Building the Simulation Layer first (this sketch)
confirmed the equation interfaces are stable BEFORE committing to a
Feed Library schema that those equations will need to plug into --
cheaper to adjust a data class now than after the Feed Library and RUP
equations are built on top of a shape that turns out wrong.

## Known Open Items (tracked, to revisit)

These are confirmed gaps or uncertainties, each already flagged in the
relevant equation's `known_discrepancies` field, collected here as a
single place to check what still needs follow-up:

- **Magnesium gestation equation number unconfirmed**
  (`scientific/minerals/magnesium.py`, `MagnesiumGestationNASEM2021`).
  The source document has a text-extraction gap around this equation
  (two consecutive "(Equation 20-402)" labels with no formula text
  between them). The FORMULA is confirmed correct against real fixture
  test data (including its step-function behavior: zero before day 190
  of gestation, a fixed BW-scaled amount after). Only the citation
  number is uncertain. **To resolve:** check a paginated copy of the
  book directly (not the plain-text extraction this project has been
  using) to find the actual equation number in that section.

## Recommended next step

Continuing through the remaining macrominerals (K, Na, Cl) and trace
minerals in the same fully-cited pattern established by calcium,
phosphorus, and magnesium.
