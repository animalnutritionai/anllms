# ANLLMS Architecture Sketch — where we are, where the Feed Library goes

## Current shape (proven by simulation/requirements_report.py)

```
knowledge/          <- KnowledgeEquation base class, Publication/SoftwareReference
                        registries. No science here, just the schema.

scientific/          <- One file per equation (or tight family of equations),
  energy/               each a KnowledgeEquation subclass that WRAPS the real
  protein/              nasem_dairy function (never reimplements it), adds
  minerals/             citation/assumptions/limitations/known_discrepancies,
  vitamins/             and returns an EquationResult.
  water/

feed_library/         <- BUILT. Ingredient knowledge object (composition,
  ingredient.py           degradability), Ration (list of Ingredient +
  ration.py               kg DM/d, aggregates to diet-level numbers), and
  rup_supply.py           rup_supply.py (independently sums per-feed
                          intestinally-digestible RUP via nd.get_feed_data()
                          -> nd.calculate_feed_data() -> nd.calculate_Dt_idRUPIn(),
                          the same real functions the full model uses
                          internally -- no full model run needed for this
                          number anymore). Verified to match the full
                          model's own Dt_idRUPIn to rel_tol=1e-6 on the
                          real lactating_cow_test scenario.

simulation/           <- AnimalState / Diet: plain data, no logic.
                        requirements_report.py composes equation results into
                        one explainable report. Now refuses (raises
                        ValueError) rather than silently miscalculating for
                        dry-cow scenarios -- see "Known Open Items" below.

decision/             <- NEW this session (Aug 2026). Diet evaluation and
                        (eventually) solving -- permanently separate from the
                        citation/calculation layers above by a ONE-WAY import
                        boundary, machine-enforced by
                        tests/test_import_boundaries.py: decision/ may import
                        FROM knowledge/, scientific/, feed_library/,
                        simulation/, but none of those may ever import FROM
                        decision/. This is a permanent architectural
                        decision, not provisional pending a repo split (no
                        repo separation planned for at least two years).
                          evaluate_diet.py  <- given a REAL ration, does it
                            meet NASEM requirements? Wraps
                            requirements_report.build_requirements_report()
                            directly, adds: (a) a hard requirement for a
                            real ration (no placeholder fallback), (b) a
                            flag when the ration's own total kg DM/d
                            diverges from the model's predicted DMI by
                            >10%, (c) per-nutrient %-of-requirement +
                            deficient/meets_or_exceeds status, sorted so
                            deficient nutrients surface first. Wired into
                            the chat tool as evaluate_diet (see below).
                          diet_request.py   <- ObjectiveSpec / IngredientBound
                            / NutrientBound / SolveRequest: the objective +
                            constraint spec the not-yet-built solve_diet
                            will consume. Validated and tested ahead of the
                            optimizer itself. Includes placeholder
                            dmi_mode / known_dmi_kg fields -- see the DMI
                            open item below before building on those.
                          solve_diet.py     <- NOT YET BUILT.
                          sensitivity.py    <- NOT YET BUILT.
```

As of this update: 35 equation files across energy (7), protein (10),
minerals (14, all 13 minerals plus supporting files), vitamins (3), and
water (1) -- 91 `KnowledgeEquation` subclasses total. (An earlier version
of this document said "12 equations mapped so far"; that was accurate at
the time it was written but is long out of date -- left here only so the
growth is visible, not as a claim about current scope.)

Test suite: 188/189 passing as of this session (up from 162/163) -- the
one failure remains the same pre-existing, unrelated stale wording
assertion in `test_magnesium.py` noted in earlier sessions, untouched by
this session's work.

## What the integration test caught

Nothing broke on the first real composition — which is itself informative:
it means the equation-by-equation interfaces (units, argument names, what
each `calculate()` needs vs. produces) were consistent enough to click
together. The one substantive thing the composed report surfaces that no
single equation could: a lactating cow's MP requirement is NOT met by
microbial protein alone (see the report's negative "partial MP balance").
That's not a bug — it's the expected, correct signal that RUP is a real
and necessary MP source, not an optional refinement.

## Diet evaluation and solving (new this session, Aug 2026)

The onboarding nutrition specialist's real use case -- generating and
checking diets for dairy farm clients -- needs more than the
citation/explanation engine above provides. Design discussion this
session settled on a small set of composable primitives the chat LLM can
call, rather than trying to enumerate every phrasing a specialist might
use:

- **`evaluate_diet`** -- BUILT. Given a real ration, is it adequate?
  (this session's deliverable, described above).
- **`solve_diet`** -- NOT YET BUILT. Least-cost / IOFC-maximizing diet
  formulation. Decided this session: treats `nd.nasem()` as a black box
  (a derivative-free global optimizer, e.g. `scipy.optimize.
  differential_evolution`, calling the REAL full model per candidate
  ration) rather than a linearized approximation -- NASEM's microbial
  protein synthesis and NEL feeding-level corrections are nonlinear
  enough to rule out a pure linear-programming approach. This mirrors
  published precedent (a 2024 J. Animal Science evaluation used the same
  SciPy differential-evolution approach against NASEM). The objective +
  constraint spec it will consume is built (`diet_request.py`, above);
  the optimizer itself is not.
- **`sweep_parameter`** -- NOT YET BUILT. Powers sensitivity/what-if
  questions (e.g. "how does the optimal diet change as corn silage NDF
  digestibility varies") and scenario-planning questions (e.g. purchase
  quantity ranges) by re-running evaluate_diet/solve_diet repeatedly with
  one input perturbed -- no new optimization logic of its own, pure
  orchestration. Real per-feed field confirmed to exist for the NDF-
  digestibility case: `Fd_DNDF48_input` in `NASEM_feed_library.csv`.
- **`explain_result`** -- covered by the existing `explain_component`
  chat tool; no new work needed.

**Important scope note on IOFC, documented in `diet_request.py`'s
docstring so it isn't lost:** with milk yield held fixed (which is how
every requirement equation in this codebase works -- they don't predict
a production RESPONSE to diet quality), maximizing income-over-feed-cost
is mathematically identical to minimizing cost; revenue is constant. A
genuine production-response version of `solve_diet` would need its own
citation-backed milk-response function -- a deliberate, separate future
addition, not something to fold in silently.

## Critical bug found and fixed (Aug 2026 session)

`scientific/vitamins/` contained three files literally named `vitamin
a.py`, `vitamin d.py`, `vitamin e.py` (spaces, not underscores), while
`simulation/mineral_vitamin_water.py` imported them as
`anllms.scientific.vitamins.vitamin_a`, `vitamin_d`, `vitamin_e` --
not merely a wrong path, but not valid Python at all (a module with a
space in its filename can't be `import`ed by that name). This import is
unconditional at module load time, so it broke the entire chain:
`mineral_vitamin_water.py` failed to import -> `requirements_report.py`
failed to import -> the live chat tool errored on every single request,
regardless of scenario. Most likely cause: a GitHub web-editor "create
file" typo (space instead of underscore), an easy slip given a
VoiceOver-only editing workflow.

**Fixed and verified end-to-end:** filenames corrected to
`vitamin_a.py` / `vitamin_d.py` / `vitamin_e.py`. **Note (confirmed via
Render deploy logs, Aug 30):** the deploy attempt for the commit that
introduced this bug (`update_failed`, "inserted updated verssions of
files") crashed on startup with exactly the predicted
`ModuleNotFoundError: No module named 'anllms.simulation.
requirements_report'` -- direct confirmation this was live-breaking, not
just theoretical. The very next commit that session ("renamed files
using underscores in place of spaces") deployed successfully and fixed
it. Render's failure-notification email for the broken commit arrived
after the fix was already live -- a real but already-resolved alert, not
a new issue.

## The Feed Library gap (mostly closed)

`feed_library/ingredient.py`, `ration.py`, and `rup_supply.py` now exist.
`ingredient.py`/`ration.py` are wired into the chat tool via
`Ration.guelph_base_diet()` (a fallback diet -- `nasem_dairy`'s own
built-in demo ration, NOT a NASEM book example -- used automatically
when a chat query doesn't specify a real ration, with an explicit
warning inserted into the report). **Note:** `evaluate_diet` (new this
session) deliberately does NOT use this fallback -- it requires a real
ration and errors otherwise, since a specialist evaluating an actual
client ration should never silently receive placeholder-diet numbers.

`protein/total_mp_supply.py` now sources RUP-derived MP supply from
`rup_supply.py` independently, rather than extracting `Dt_idRUPIn` from
a full model run. **Still open:** the microbial half of the same
equation (`Du_idMiTP_g`) still requires a full model run, because
`MicrobialCrudeProteinNASEM2021`'s own inputs (rumen-degradable protein
intake, rumen-digested NDF/starch intake) aren't yet independently
mapped in this codebase. This is a narrower, different gap than before
-- tracked below.

## Known Open Items (tracked, to revisit)

These are confirmed gaps or uncertainties, each already flagged in the
relevant equation's `known_discrepancies` field (where applicable),
collected here as a single place to check what still needs follow-up.

**DMI: needs an actual-vs-predicted mode decision (found Aug 2026,
scheduled for a dedicated next session).** Every requirement/supply/
balance calculation currently ALWAYS predicts DMI via the cited
equations (Eq. 2-1 or diet-aware Eq. 2-2), even when the caller already
knows the cow's actual measured intake. This surfaced concretely when
`evaluate_diet` flagged an 11.3% "mismatch" on `nasem_dairy`'s own
`lactating_cow_test` demo scenario -- turned out the demo itself is
configured with `equation_selection['DMIn_eqn']=0`, meaning the
reference software's own official behavior for that scenario is to use
a directly-given target DMI and skip prediction entirely, not to
predict and then compare. Our code has no equivalent mode yet.

Expected real-world usage (per working discussion, Aug 2026): the
onboarding nutrition specialist will have actual measured/estimated DMI
for a client's cow in the large majority of cases (~95% estimated) and
will want that value used directly, with prediction reserved for the
minority of cases where no real number is available. This is NOT a
small fix -- it's a mode decision that needs to be threaded consistently
through `calculate_lactating_cow_requirements`, `evaluate_diet`, and
(once built) every candidate-ration call `solve_diet` makes, plus a
clear way of telling the end user which mode was used for any given
number (measured vs. predicted) so the two are never presented as
equivalent. `diet_request.py`'s `dmi_mode`/`known_dmi_kg` fields exist
as placeholders for this but are not yet wired to any logic. Scheduled
as a dedicated next-session focus, not something to bolt on
incrementally.

**Equation citations still needing a direct paginated-book read:** NONE
remaining as of the citation-verification session. Iodine (Eq. 20-455)
was the last item in this category and was resolved that session (see
below) -- every equation citation in the codebase has now either been
directly confirmed against a paginated book screenshot, or confirmed as
having no separate numbered equation to find (see the next item).

**Resolved in the citation-verification session (Aug 2026), confirmed by
direct paginated-book screenshots provided by the user:**
- **Iodine requirement, Eq. 20-455** (`minerals/iodine.py`) -- the book's
  criteria table matches this file's implementation and
  `nasem_dairy.calculate_An_I_req()` exactly for the adult/non-calf
  branch (`0.216*BW^0.528 + 0.1*MilkProd`). Citation upgraded from
  "confident attribution by position" to fully confirmed. **New known
  discrepancy found in the same screenshot:** the book's criteria table
  gates the (unimplemented) calf branch on TWO conditions
  (`An_StatePhys="Calf"` AND `Dt_DMIn_ClfLiq>0`), while
  `nasem_dairy.calculate_An_I_req()` checks only `An_StatePhys=='Calf'`.
  Zero-impact today since the calf branch isn't implemented in this
  codebase; documented in case it ever is, with software taking
  precedence per NASEM's own stated book/code precedence.
- **Vitamin A (Eq. 20-491), Vitamin D (Eq. 20-493), Vitamin E (Eq.
  20-495)** -- all three formulas match the code exactly, including
  Vitamin E's three-tier branching and pasture credit. Citations updated
  to drop the earlier "confident attribution by position" hedge.
- **Magnesium gestation (Eq. 20-402) and growth (Eq. 20-401)** -- the
  screenshot independently reproduced the exact "duplicate formula text"
  extraction artifact this document already predicted, confirming the
  earlier structural-cross-reference resolution. No code change needed.
- **Potassium urinary maintenance term, Ur_K_m -- now Eq. 20-430**
  (`minerals/potassium.py`), confirmed by direct paginated read (was
  previously cited only as "not separately numbered"). **New known
  discrepancy found in the same screenshot:** the book's own criteria
  table for Eq. 20-430 appears to read `>0 kg/d milk -> 0.07*BW` and
  `0 kg/d milk -> 0.2*BW` -- the opposite direction from what
  `nasem_dairy`'s `calculate_Ur_K_m()` implements (0.2*BW when lactating,
  0.07*BW when dry). Per project decision, the platform follows the
  software's direction, citing NASEM's own stated precedence for exactly
  this kind of conflict (Ch. 20, "Nutrient Supply Model" intro): *"Should
  there be differences between the description of the model herein and
  the actual model code written in R, the latter is more likely to be
  correct... The R code was developed and verified over a 4-year period
  and thus should generally be the more reliable source."* Documented in
  `known_discrepancies` (and therefore surfaced to end users via
  `explain()`), not silently resolved either way. A second, clearer
  paginated read of that specific table cell would still be useful
  confirmation, though it would not change the computed result.

**Confirmed absent (no numbered equation exists) -- wording resolved in
the citation-verification session, distinct from the "still needing a
read" category above since no further reading will surface a number
that isn't there:**
- **Milk net protein target conversion** (`protein/milk_net_protein.py`)
  -- `Trg_Mlk_NP_g = MilkProd x TPp / 100`. Directly searched Chapter 6
  and the Chapter 20 appendix around Equations 20-208 through 20-214
  (the EAA-based predictive milk protein equations) and ruled those out.
  That session's change: the file's `known_discrepancies` previously said
  to "treat as unresolved... until someone checks directly against a
  paginated copy" -- that check already happened, so the wording now
  states the absence as CONFIRMED, not open.
- **Microbial MP supply conversion** (`protein/microbial_mp_supply.py`)
  -- the 80% x 82.4% MCP-to-MP step. Chapter 6 narrative states the
  coefficients explicitly; the appendix jumps from Eq. 20-79 to Eq. 20-80
  without a numbered display equation for this specific step. This file's
  wording was already accurate and needed no change that session.

**`SoftwareReference` docstring inconsistency -- RESOLVED.** The
docstring previously claimed the reference software "is NEVER called at
runtime," which contradicted actual behavior (every equation's
`calculate()` does call the real `nasem_dairy` function at runtime -- the
"wrap, don't reimplement" principle this whole project is built around).
Also user-facing, not just internal: the `role` field's old default text
("Cross-validation / equation-mapping reference only. Not used at
runtime.") is rendered directly in `explain()` output for all 91 equation
files (none override the default), so end users were being told this
claim directly. Fixed: docstring rewritten to describe the actual
three-part role (mapping/citation, cross-validation testing, AND the
actual runtime call), `role` default corrected, and the `explain()`
label changed from "Cross-validated against:" to "Implementation
source:". Reproducibility is achieved via pinning
`version_used_for_mapping` to a fixed `nasem_dairy` release, not by
avoiding runtime calls.

**Frame/body reserve growth** (Frm/Rsrv terms for both MP and NEL) --
still not built (deferred, not independently cited); documentation
across four files (`protein/mp_maintenance.py`,
`protein/milk_mp_requirement.py`, `energy/maintenance.py`,
`energy/lactation.py`) states explicitly that this is a CONFIRMED,
DELIBERATE deferral, not an oversight. Zero-impact for a standard
mature, non-growing lactating cow (the platform's current actual use
case) since `Frm_Gain`/`Rsrv_Gain` default to 0 and the terms vanish.
Building it would require independently mapping nasem_dairy's ~10-
function growth-partitioning chain in `body_composition.py`
(`Trg_FrmGain`/`Trg_RsrvGain` -> `NPgain` -> `CPgain` -> `Fatgain`, split
frame vs. reserve) before `Frm_NEgain`/`Rsrv_NEgain` (Eq. 3-20c) or the
parallel MP terms could be independently cited. Recommended to defer
until a heifer-growth or deliberate body-condition-change use case
actually enters scope, rather than build speculatively now.

**Dry-cow scenarios -- guard in place.** `requirements_report.py` only
implements lactating-cow DMI equations (Eq. 2-1 / Eq. 2-2); the
reference software's separate dry-cow DMI equations
(`Dt_DMIn_DryCow1/2`) are not mapped in this codebase. This was already
documented at the individual-equation level
(`energy/dmi_lactating.py`'s `applicability` field), but nothing
enforced it at the orchestration layer -- a `milk.yield_kg <= 0` scenario
would have silently run the wrong DMI equation, and every downstream
requirement/supply/balance figure would have inherited that error with
no warning surfaced. `build_requirements_report()` raises a clear
`ValueError` for `milk.yield_kg <= 0` instead, explaining why, rather
than returning a plausible-looking but scientifically invalid report.

**Mineral/vitamin supply equations** still extract their value from the
shared full-model run rather than independently summing per-ingredient
contributions via the Feed Library. **RUP supply** no longer has this
gap (see "The Feed Library gap" above) -- but the total-MP-supply
equation's microbial half still does, pending independent mapping of
rumen-degradable-protein and rumen-digestion inputs.

**Diet solver** -- design settled this session (`diet_request.py`,
above); optimizer itself not yet built, blocked behind the DMI mode
decision (also above).

**Life-stage scope check:** before considering heifer, growing-
lactating, or other new life-stage classes, confirmed the mature
non-growing lactating cow scope itself isn't fully closed out yet (the
dry-cow DMI gap above was the concrete finding). Also investigated
whether the several files that hardcode `An_StatePhys="Lactating Cow"`
(scurf, fecal endogenous, urinary endogenous MP, iodine, water) were a
similar silent-wrong-branch bug -- traced each into `nasem_dairy` and
confirmed they are NOT: those functions only branch on `Calf` vs.
non-`Calf`, or on `Trg_MilkProd`/`An_Parity_rl` directly, so the
hardcoded string is functionally inert in every case checked. No fix
needed there. Recommendation: finish closing gaps in the current
mature-lactating-cow scope (microbial-supply inputs, DMI mode, Frame/
Reserve if ever needed) before adding new life-stage classes, rather
than expanding breadth before depth.

## Deployment (see README.md for full current details)

**Current, live, and confirmed working (verified via Render MCP, Aug
30):** Render (`anllms-chat` service, id `srv-da7jf5jbc2fs73d2bpa0`)
running `chat/server.py`, which routes model calls through a self-hosted
LiteLLM proxy (also on Render: `litellm:main-latest`, not Cloud Run --
correcting an earlier assumption in this doc) rather than calling
`api.anthropic.com` directly. Model selectable via the `ANLLMS_MODEL` env
var; the `gemini-flash` alias currently points at a deprecated
underlying model and needs a proxy-side fix -- Mistral aliases are a
working temporary substitute.

**Aug 28 deploy failure, root-caused and confirmed already resolved:**
the vitamin-filename bug (see "Critical bug found and fixed" above)
caused one deploy (`update_failed`, commit "inserted updated verssions
of files") to crash on startup with `ModuleNotFoundError`. Render's
notification email for this arrived after the fix was already live via
the next commit. No outstanding deploy issue as of this session.

**Abandoned before going live:** PythonAnywhere (free tier hit its
512MB disk quota repeatedly due to `nasem_dairy`'s dependency tree). The
`deploy/` directory and its PythonAnywhere-specific instructions have
been removed from the repo. GitHub Codespaces remains useful for
accessible (screen-reader-friendly) local dev/testing -- see below -- but
is not the production deployment path.

*(The detailed PythonAnywhere walkthrough, Codespaces accessibility
notes, and serialization-fix history that previously lived in this
section as several separate "Session update" entries have been folded
into this summary and into `README.md`'s "Deployment history" section,
to stop this document from accumulating superseded, contradictory status
entries. If you need the original blow-by-blow debugging narrative for
any of those sessions, it's in this file's git history.)*

### Accessible chat testing via Codespaces (screen-reader workflow)

GitHub Codespaces' own IDE (editor UI + embedded terminal) is difficult
to navigate with JAWS/VoiceOver -- dense, dynamically-updating dashboards
are harder for screen readers than simpler, page-based UIs. Render and
Replit's dashboards had the same problem. Running a local server was
ruled out (unwilling to run project code/dependencies on a personal
laptop). The working approach: use Codespaces purely for its port
forwarding, bypassing its IDE entirely, to reach the plain
`chat/static/index.html` page directly.

`server.py` binds to `host="0.0.0.0"` (required for Codespaces port
forwarding). With `ANTHROPIC_API_KEY` -- or, since the LiteLLM migration,
`LITELLM_API_KEY` / `LITELLM_BASE_URL` -- set as repo-level Codespace
secrets:

```bash
pip install -e ".[chat]"
python -m chat.server
```

This has been run successfully at least once; it has not been
stress-tested with varied real conversations.
