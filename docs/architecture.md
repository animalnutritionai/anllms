# ANLLMS Architecture Sketch — where we are, where the Feed Library goes

## Current shape (proven by simulation/requirements_report.py)

```
knowledge/          <- KnowledgeEquation base class, Publication/SoftwareReference
                        registries. No science here, just the schema.

scientific/          <- One file per equation (or tight family of equations),
  energy/               each a KnowledgeEquation subclass that WRAPS the real
    dmi_measured.py       NEW this session (Sept 2026). NOT a predictive
                          equation -- wraps a caller-supplied (measured/
                          estimated) DMI directly, mirroring the reference
                          software's own DMIn_eqn == 0 mode. See "DMI
                          actual-vs-predicted mode" below.
  protein/              nasem_dairy function (never reimplements it), adds
  minerals/             citation/assumptions/limitations/known_discrepancies,
  vitamins/             and returns an EquationResult.
  water/

feed_library/         <- BUILT. Ingredient knowledge object (composition,
  ingredient.py           degradability), Ration (list of Ingredient +
  ration.py               kg DM/d, aggregates to diet-level numbers).
  rup_supply.py           rup_supply.py independently sums per-feed
                          intestinally-digestible RUP via the real
                          nd.get_feed_data() -> nd.calculate_feed_data()
                          -> nd.calculate_Dt_idRUPIn() pipeline -- the
                          same real functions the full model uses
                          internally -- no full model run needed for this
                          number. Verified to match the full model's own
                          Dt_idRUPIn to rel_tol=1e-6 on the real
                          lactating_cow_test scenario.
  microbial_substrate.py  Independently derives the four inputs
                          MicrobialCrudeProteinNASEM2021 needs
                          (An_RDPIn, An_RDP, Rum_DigNDFIn, Rum_DigStIn)
                          from the same per-feed pipeline -- none of
                          these depend on the iterative rumen-fill/pH
                          submodel, only on diet-total nutrient intake
                          sums, so no full model run is needed here
                          either. Verified to rel_tol=1e-6 against the
                          full model's own An_RDPIn/An_RDP/
                          Rum_DigNDFIn/Rum_DigStIn/Du_MiCP_g on
                          lactating_cow_test.
  _feed_data.py           Internal helper (build_complete_feed_data())
                          factoring out the shared nd.get_feed_data() ->
                          nd.calculate_feed_data() setup so it's called
                          in one place, not duplicated between
                          rup_supply.py and microbial_substrate.py.

simulation/           <- AnimalState / Diet: plain data, no logic.
                        requirements_report.py composes equation results into
                        one explainable report. Refuses (raises ValueError)
                        rather than silently miscalculating for dry-cow
                        scenarios -- see "Known Open Items" below.
                        build_requirements_report() NOW SUPPORTS a
                        dmi_mode parameter ("predict" | "actual") -- see
                        "DMI actual-vs-predicted mode: RESOLVED" below.
                        No changes were needed to nasem_model_bridge.py:
                        it already always calls nd.nasem() with
                        DMIn_eqn=0, accepting whatever dmi_kg value it's
                        handed regardless of how that value was produced.

decision/             <- Diet evaluation and (eventually) solving --
                        permanently separate from the citation/calculation
                        layers above by a ONE-WAY import boundary,
                        machine-enforced by tests/test_import_boundaries.py:
                        decision/ may import FROM knowledge/, scientific/,
                        feed_library/, simulation/, but none of those may
                        ever import FROM decision/. This is a permanent
                        architectural decision, not provisional pending a
                        repo split (no repo separation planned for at
                        least two years).
                          evaluate_diet.py  <- given a REAL ration, does it
                            meet NASEM requirements? Wraps
                            requirements_report.build_requirements_report()
                            directly, adds: (a) a hard requirement for a
                            real ration (no placeholder fallback), (b) a
                            flag when the ration's own total kg DM/d
                            diverges from the DMI value actually used by
                            >10% -- worded differently depending on
                            dmi_mode (see below), (c) per-nutrient
                            %-of-requirement + deficient/meets_or_exceeds
                            status, sorted so deficient nutrients surface
                            first. NOW SUPPORTS dmi_mode/known_dmi_kg,
                            passed straight through to
                            build_requirements_report(). Wired into the
                            chat tool as evaluate_diet (see below).
                          diet_request.py   <- ObjectiveSpec / IngredientBound
                            / NutrientBound / SolveRequest: the objective +
                            constraint spec the not-yet-built solve_diet
                            will consume. Validated and tested ahead of the
                            optimizer itself. dmi_mode / known_dmi_kg are
                            NO LONGER PLACEHOLDERS -- the decision they were
                            waiting on is resolved (see below); solve_diet
                            is expected to honor them the same way
                            evaluate_diet now does, once built.
                          solve_diet.py     <- NOT YET BUILT. Next planned
                            piece of work.
                          sensitivity.py    <- NOT YET BUILT.
```

As of this update: 36 equation files across energy (8, including the new
`dmi_measured.py`), protein (10), minerals (14, all 13 minerals plus
supporting files), vitamins (3), and water (1) -- 92 `KnowledgeEquation`
subclasses total. (An earlier version of this document said "12 equations
mapped so far"; that was accurate at the time it was written but is long
out of date -- left here only so the growth is visible, not as a claim
about current scope.)

Test suite: **213/214 passing** as of this session (Sept 2026, up from
195/196) -- the one failure remains the same pre-existing, unrelated
stale wording assertion in `test_magnesium.py` noted in earlier sessions,
untouched by this session's work. The 18 new passing tests this session:
5 in `tests/test_dmi_measured.py` (new file), 5 new cases in
`tests/test_requirements_report.py`, 4 new cases in
`tests/test_evaluate_diet.py`, 6 new cases in `tests/test_chat_tools.py`
(net +18 after accounting for one pre-existing test's wording tweak).

## What the integration test caught

Nothing broke on the first real composition — which is itself informative:
it means the equation-by-equation interfaces (units, argument names, what
each `calculate()` needs vs. produces) were consistent enough to click
together. The one substantive thing the composed report surfaces that no
single equation could: a lactating cow's MP requirement is NOT met by
microbial protein alone (see the report's negative "partial MP balance").
That's not a bug — it's the expected, correct signal that RUP is a real
and necessary MP source, not an optional refinement.

## DMI actual-vs-predicted mode: RESOLVED (Sept 2026 session)

**The decision, and what it closes:** `build_requirements_report()` and
`evaluate_diet()` both now accept `dmi_mode: Literal["predict", "actual"]
= "predict"` and `known_dmi_kg: float | None = None`.

- **`dmi_mode="predict"`** (default, unchanged behavior) -- DMI is
  predicted via Eq. 2-1 or diet-aware Eq. 2-2, exactly as before this
  session. Used when no real measured/estimated DMI is available.
- **`dmi_mode="actual"`** -- DMI prediction is skipped entirely.
  `known_dmi_kg` is wrapped by the new `MeasuredDMINASEM2021`
  (`scientific/energy/dmi_measured.py`) and fed to every downstream
  calculation exactly as a predicted value would be. This mirrors the
  reference software's own `DMIn_eqn == 0` mode (use the caller-supplied
  `Trg_Dt_DMIn` directly) -- not an invented shortcut; `nasem_model_bridge.py`
  has in fact always called `nd.nasem()` this way, so no change was
  needed there. Preferred whenever a real measured/estimated DMI is
  available -- per project decision (Aug 2026 working discussion),
  expected to be the common case (~95%) for the onboarding specialist's
  real client cows, with "predict" reserved as the fallback.

**Why a citation-backed equation object for a pass-through value:** so
`explain_component("dmi")` has something real to describe in actual mode
too, using the exact same explain()/citation machinery as every predicted
path, rather than a special-cased blank. Its citation documents plainly
that no numbered book equation applies -- this is the software's
`DMIn_eqn==0` mode, not a citation gap.

**Mismatch-warning wording is now mode-aware.** In "predict" mode, a
ration-total-vs-DMI-used mismatch is a real NASEM-modeling subtlety
(predicted intake, not the ration's own total, drives every downstream
number). In "actual" mode, the same mismatch means the ration as entered
doesn't total to what the cow is reported to actually be eating -- a
data-entry question, not a modeling one. `evaluate_diet()` now emits
different warning text for each case so a specialist is never told a
data-entry problem is a modeling uncertainty or vice versa.

**Chat tool surface:** both `calculate_lactating_cow_requirements` and
`evaluate_diet` tool schemas (`chat/tools.py`) gained optional
`dmi_mode` (enum) and `known_dmi_kg` fields, with tool descriptions
instructing the LLM to ask the user whether they already know the cow's
actual DMI before defaulting to prediction. Default stays `"predict"`,
so no existing caller breaks.

**One open question, deliberately left to solve_diet's own build
session, not resolved here:** if `dmi_mode="actual"` and a future
optimizer explores candidate rations materially different from the one
`known_dmi_kg` was measured against, a fixed measured value may not
reflect what the cow would actually eat on a very different diet.
`MeasuredDMINASEM2021`'s own `limitations` field and `diet_request.py`'s
module docstring both flag this; it's a solver-design question (how far
is the optimizer allowed to roam from the current ration) rather than
something the single-ration `evaluate_diet` case needs to solve.

## Diet evaluation and solving

The onboarding nutrition specialist's real use case -- generating and
checking diets for dairy farm clients -- needs more than the
citation/explanation engine above provides. Design discussion settled on
a small set of composable primitives the chat LLM can call, rather than
trying to enumerate every phrasing a specialist might use:

- **`evaluate_diet`** -- BUILT, and now DMI-mode-aware (see above).
- **`solve_diet`** -- NOT YET BUILT. Next planned piece of work now that
  the DMI mode decision (previously the stated blocker) is resolved.
  Least-cost / IOFC-maximizing diet formulation. Decided: treats
  `nd.nasem()` as a black box (a derivative-free global optimizer, e.g.
  `scipy.optimize.differential_evolution`, calling the REAL full model
  per candidate ration) rather than a linearized approximation --
  NASEM's microbial protein synthesis and NEL feeding-level corrections
  are nonlinear enough to rule out a pure linear-programming approach.
  This mirrors published precedent (a 2024 J. Animal Science evaluation
  used the same SciPy differential-evolution approach against NASEM).
  The objective + constraint spec it will consume is built
  (`diet_request.py`, above, dmi_mode/known_dmi_kg no longer
  placeholders); the optimizer itself is not.
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

## Recurring workflow risk: file-upload naming (Sept 2026 session)

**This is the same category of bug as "Critical bug found and fixed"
above, and it recurred this session in a new form -- worth a permanent
note since it has now happened multiple times across different
mechanisms.** This session's file-delivery workflow (Claude generates a
file, presents it via a download/share UI, person saves it into Working
Copy on iOS, then moves/renames it into place via GitHub's web editor)
produced two distinct new failure modes before landing correctly:

1. **Display-name-as-filename:** the file-sharing UI shows a
   human-readable title with underscores replaced by spaces (e.g.
   "dmi measured" instead of `dmi_measured.py`). When that displayed
   name was used as the actual saved filename, files landed with spaces
   in place of underscores.
2. **New-file-instead-of-overwrite:** when a re-uploaded file's name
   didn't exactly match the file it was meant to replace (e.g. a
   trailing space, or copying the path text with extra whitespace), git/
   GitHub created a brand-new file alongside the old one instead of
   replacing it -- leaving the OLD, stale content live at the correctly-
   named path while the NEW content sat under a wrongly-named sibling
   file. This is dangerous specifically because the correctly-named file
   still exists and still imports fine -- nothing errors, it's just
   silently running old logic.

**Working fix, adopted this session and now standard practice:** before
presenting each file, state its exact intended repo destination path in
its own standalone code block (e.g. `anllms/scientific/energy/
dmi_measured.py`), immediately followed by that one file -- one
path-then-file pair per file, not a batched list at the end. This gives
a copy-pasteable, unambiguous exact filename immediately next to the
file it belongs to. **Verification discipline that caught both failure
modes above:** after any file delivery + manual move/rename, re-pull the
repo fresh (or `git clone` for full history) and check (a) each file's
exact byte content against what was generated, (b) no stray duplicate or
misnamed files exist at the target directories or left at repo root, and
(c) `git diff --stat` against the pre-session commit to confirm nothing
outside the intended file set was touched -- catches accidental deletions
elsewhere, not just naming problems in the intended files.

## The Feed Library gap (closed, for MP supply)

`feed_library/ingredient.py`, `ration.py`, `rup_supply.py`,
`microbial_substrate.py`, and `_feed_data.py` exist. `ingredient.py`/
`ration.py` are wired into the chat tool via `Ration.guelph_base_diet()`
(a fallback diet -- `nasem_dairy`'s own built-in demo ration, NOT a
NASEM book example -- used automatically when a chat query doesn't
specify a real ration, with an explicit warning inserted into the
report). **Note:** `evaluate_diet` deliberately does NOT use this
fallback -- it requires a real ration and errors otherwise, since a
specialist evaluating an actual client ration should never silently
receive placeholder-diet numbers.

`protein/total_mp_supply.py` sources BOTH halves of total MP supply
independently -- RUP-derived (via `rup_supply.py`) and microbial-derived
(via `microbial_substrate.py` feeding the unchanged, already-cited
`MicrobialCrudeProteinNASEM2021` / `MicrobialMPSupplyNASEM2021`).
Neither half requires a full `nd.nasem()` model run anymore.
`animal`/`milk` parameters on `TotalMPSupplyNASEM2021.calculate()` are
optional (kept only for call-signature backward compatibility with
`requirements_report.py`) -- the independent path never touches either.
`model_output`, if a caller happens to have one (e.g.
`requirements_report.py`, which runs one anyway for other
requirement/supply figures), is used ONLY as an optional cross-check
surfaced in `inputs_used` -- it no longer supplies the returned value.

## Known Open Items (tracked, to revisit)

These are confirmed gaps or uncertainties, each already flagged in the
relevant equation's `known_discrepancies` field (where applicable),
collected here as a single place to check what still needs follow-up.

**DMI actual-vs-predicted mode -- RESOLVED this session.** See dedicated
section above. No longer an open item.

**Equation citations still needing a direct paginated-book read:** NONE
remaining as of the citation-verification session. Iodine (Eq. 20-455)
was the last item in this category and was resolved that session -- every
equation citation in the codebase has now either been directly confirmed
against a paginated book screenshot, or confirmed as having no separate
numbered equation to find (see the next item).

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
  this kind of conflict (Ch. 20, "Nutrient Supply Model" intro): the book
  states that where the book description and the R code disagree, the R
  code -- developed and verified over a 4-year period -- should generally
  be treated as the more reliable source. Documented in
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
- **Microbial MP supply conversion** (`protein/microbial_mp_supply.py`)
  -- the 80% x 82.4% MCP-to-MP step. Chapter 6 narrative states the
  coefficients explicitly; the appendix jumps from Eq. 20-79 to Eq. 20-80
  without a numbered display equation for this specific step.

**`SoftwareReference` docstring inconsistency -- RESOLVED.** The
docstring previously claimed the reference software "is NEVER called at
runtime," which contradicted actual behavior (every equation's
`calculate()` does call the real `nasem_dairy` function at runtime -- the
"wrap, don't reimplement" principle this whole project is built around).
Fixed: docstring rewritten to describe the actual three-part role
(mapping/citation, cross-validation testing, AND the actual runtime
call), `role` default corrected, and the `explain()` label changed from
"Cross-validated against:" to "Implementation source:". Reproducibility
is achieved via pinning `version_used_for_mapping` to a fixed
`nasem_dairy` release, not by avoiding runtime calls.

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
(`Dt_DMIn_DryCow1/2`) are not mapped in this codebase. `build_
requirements_report()` raises a clear `ValueError` for `milk.yield_kg <=
0` instead of returning a plausible-looking but scientifically invalid
report.

**Mineral/vitamin supply equations** still extract their value from the
shared full-model run rather than independently summing per-ingredient
contributions via the Feed Library -- this is now the ONLY remaining
supply-side gap of this kind. RUP supply and microbial-supply inputs no
longer have this gap -- both halves of total MP supply are independently
computed.

**Diet solver** -- design settled (`diet_request.py`, above); the DMI
mode decision that was blocking it is now resolved (see above). Next
planned piece of work.

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
mature-lactating-cow scope (mineral/vitamin supply, Frame/Reserve if
ever needed) before adding new life-stage classes, rather than expanding
breadth before depth.

## Deployment

**Current, live, and confirmed working (verified via Render MCP, Aug
30):** Render (`anllms-chat` service, id `srv-da7jf5jbc2fs73d2bpa0`)
running `chat/server.py`, which routes model calls through a self-hosted
LiteLLM proxy (also on Render: `litellm:main-latest`, NOT Cloud Run)
rather than calling `api.anthropic.com` directly. **Note: README.md
still describes the proxy as being on Cloud Run as of this session --
that correction has not yet been applied to README.md and remains an
open documentation task**, separate from this file (which is correct).
Model selectable via the `ANLLMS_MODEL` env var; the `gemini-flash`
alias currently points at a deprecated underlying model and needs a
proxy-side fix -- Mistral aliases are a working temporary substitute.

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
