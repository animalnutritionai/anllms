# Citations

This project cites two different kinds of source, and they are kept
separate on purpose so a reader can never mistake one for the other.

- **Part A — Equations.** Every coefficient, threshold, or formula in
  `anllms/scientific/`, `anllms/feed_library/`, etc. is backed by a
  `Publication` + `Citation` object defined in code (see
  `anllms/knowledge/models.py`) and registered in
  `anllms/knowledge/publications.py`. That registry is the source of
  truth for equation citations — this file does not duplicate it.
  Read it directly for the full list (currently NASEM Dairy 2021, NRC
  Dairy 2001, NASEM Beef 2016, and the `nasem_dairy` reference
  software).

- **Part B — Methods, precedents, and project decisions used by the
  decision layer** (`anllms/decision/`: `evaluate_diet.py`,
  `solve_diet.py`, `sensitivity.py`). These aren't equation sources —
  they're the optimization method itself, prior work that informed how
  we're applying it, and our own unforced design choices. Listed below
  because none of them fit the equation-citation schema in Part A.

---

## Part B1 — Method

**Storn, R., Price, K. (1997).** "Differential Evolution – A Simple
and Efficient Heuristic for Global Optimization over Continuous
Spaces." *Journal of Global Optimization*, 11, 341–359.

The optimization algorithm itself, as implemented by
`scipy.optimize.differential_evolution` and used in `solve_diet.py` to
search candidate rations. Confirmed directly against the published
paper (volume, pages, and abstract all verified) rather than a
secondary citation of it.

## Part B2 — Precedents (prior applications to dairy diet formulation)

These informed the design of `solve_diet.py` but are not themselves
cited for any equation or coefficient.

- **Innes, D., Fieguth, B., Kedzierski, P., Cant, J. (2024).** "194
  Evaluation of a method to optimize diets of individual dairy cows to
  maximize income over feed cost." *Journal of Animal Science*, 102
  (Supplement_3), 352–353. Conference abstract. DOI:
  10.1093/jas/skae234.401. Centre for Nutrition Modelling, Department
  of Animal Bioscience, University of Guelph — the same research group
  that built the `nasem_dairy` reference software this project wraps,
  which is worth noting as direct provenance, not just topical
  relevance. Used SciPy's differential evolution algorithm to maximize
  predicted income over feed cost by adjusting ingredient inclusion
  rates, compared against observed values for the same cows. Its
  conclusion is a caution, not an endorsement: it finds a real,
  practically-sized gap between the model's predicted performance and
  what was actually observed for individual cows, and says that gap
  needs to be reduced — for example by reparameterizing the NASEM model
  itself — before an optimizer should be trusted to auto-formulate
  diets. That caution applies directly to this project's
  `solve_diet.py` (see its module docstring's own KNOWN LIMITATION
  section, which restates this in the code itself, not just here).
- **Campos, L.M., Ringer, H., Chung, M., Hanigan, M.D. (2023).**
  "Application of a mathematical framework for the optimization of
  precision-fed dairy cattle diets." *Animal*, 17, Article 101001. DOI:
  10.1016/j.animal.2023.101001. Used a compact, vectorized version of
  the 2021 NASEM dairy model (the same edition this project wraps) to
  optimize rations for maximum profit via non-linear programming with
  both linear and non-linear constraints, tested against real
  Virginia Tech dairy herd data. Confirmed by three independent
  sources, including the Innes et al. (2024) abstract above, which
  cites this exact paper as its own dairy precedent — a useful
  cross-check that both entries point to the same real, dairy-specific
  prior work rather than a mismatch.

Both entries are now fully confirmed (author, venue, DOI each checked
against at least two independent sources) — no longer leads.

## Part B3 — Project design decisions (not sourced from any publication)

These are choices this project made, not results copied from NASEM or
any paper. Recorded here so a reader never mistakes a design decision
for a cited scientific finding.

- **Relative nutrient floors in `NutrientBound`** (e.g. "at least 105%
  of MP requirement"). Whether to recompute the requirement fresh
  against each candidate ration the solver tries, or lock it to one
  value taken from a baseline ration, is a solver-design choice with
  no single correct answer from the literature. The platform exposes
  both as an explicit user choice (`per_candidate` vs.
  `baseline_locked` on `SolveRequest`) rather than picking one
  silently. See `anllms/decision/diet_request.py` for the
  implementation and the plain-language explanation text the chat
  assistant uses to describe the tradeoff to a user.
