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

feed_library/         <- BUILT (was "planned, not yet built" in an earlier
  ingredient.py           version of this doc). Ingredient knowledge object
  ration.py               (composition, degradability) and Ration (list of
                          Ingredient + kg DM/d, aggregates to diet-level
                          numbers). RUP-derived MP supply still comes from
                          the shared full-model run rather than being
                          independently summed per-ingredient here -- see
                          "Known Open Items" below.

simulation/           <- AnimalState / Diet: plain data, no logic.
                        requirements_report.py composes equation results into
                        one explainable report.
```

As of this update: 35 equation files across energy (7), protein (10),
minerals (14, all 13 minerals plus supporting files), vitamins (3), and
water (1) -- 91 `KnowledgeEquation` subclasses total. (An earlier version
of this document said "12 equations mapped so far"; that was accurate at
the time it was written but is long out of date -- left here only so the
growth is visible, not as a claim about current scope.)

## What the integration test caught

Nothing broke on the first real composition — which is itself informative:
it means the equation-by-equation interfaces (units, argument names, what
each `calculate()` needs vs. produces) were consistent enough to click
together. The one substantive thing the composed report surfaces that no
single equation could: a lactating cow's MP requirement is NOT met by
microbial protein alone (see the report's negative "partial MP balance").
That's not a bug — it's the expected, correct signal that RUP is a real
and necessary MP source, not an optional refinement.

## The Feed Library gap (partially closed)

`feed_library/ingredient.py` and `feed_library/ration.py` now exist and
are wired into the chat tool via `Ration.guelph_base_diet()` (a fallback
diet -- `nasem_dairy`'s own built-in demo ration, NOT a NASEM book
example -- used automatically when a chat query doesn't specify a real
ration, with an explicit warning inserted into the report).

**Still open:** the planned `feed_library/rup_supply.py` (independently
summing ingredient RUP intake x ingredient intestinal RUP digestibility)
has not been built. `protein/total_mp_supply.py` currently extracts
`Dt_idRUPIn` from a full `nasem_dairy` model run instead -- the same
scope decision already documented for mineral/vitamin supply (see below).
This is a deliberate, documented gap, not an oversight -- a single
diet-level "RUP digestibility %" would be a simplification the project's
own rules argue against.

## Known Open Items (tracked, to revisit)

These are confirmed gaps or uncertainties, each already flagged in the
relevant equation's `known_discrepancies` field, collected here as a
single place to check what still needs follow-up.

**Equation citations still needing a direct paginated-book read** (not
yet confirmed, only structurally/positionally attributed):
- **Iodine requirement, Eq. 20-455** (`minerals/iodine.py`) -- formula
  text has a source-extraction gap; position between the "Iodine" header
  and the confirmed balance equation (20-456) makes the number confident
  but not directly read.
- **Milk net protein target conversion** (`protein/milk_net_protein.py`)
  -- `Trg_Mlk_NP_g = MilkProd x TPp / 100`. Searched directly against the
  book's Eq. 20-208 through 20-214 (the EAA-based predictive milk protein
  equations) and confirmed those are NOT it -- this simple target
  conversion does not appear to have its own display-numbered equation
  in the appendix.
- **Microbial MP supply conversion** (`protein/microbial_mp_supply.py`)
  -- the 80% x 82.4% MCP-to-MP step. Chapter 6 narrative states the
  coefficients explicitly; the appendix jumps from Eq. 20-79 to Eq. 20-80
  without a numbered display equation for this specific step.

**Resolved this session (Aug 2026), confirmed by direct paginated-book
screenshots provided by the user:**
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

**Architecture documentation inconsistency found this session, not yet
resolved:** `knowledge/models.py`'s `SoftwareReference` docstring states
a software reference "is NEVER called at runtime by the platform's
calculation engine... used for (1) mapping/extracting... and (2)
cross-validating." In practice, every equation file's `calculate()`
method does call the real `nasem_dairy` function directly at runtime
(`import nasem_dairy as nd; nd.calculate_X(...)`) -- this is in fact the
"wrap, don't reimplement" principle this whole project is built around.
Either the docstring is describing an earlier/different design that was
superseded, or it's aspirational and never matched the actual
implementation. Needs a decision: fix the docstring to match reality, or
explain why the discrepancy is intentional. Flagged, not resolved.

**Frame/body reserve growth** (Frm/Rsrv terms for both MP and NEL) --
still come from the reference model directly, not independently cited.
Unlike gestation, their equation numbers were not found in the same
requirements-chapter sections of the book searched so far; likely belong
to NASEM's separate Growth chapter (empty body gain, retained energy,
etc.), not yet mapped. Zero-impact for a standard mature cow with no
explicit frame/reserve gain target; affects heifer-growth or deliberate
body-condition-change scenarios.

**Mineral/vitamin and RUP supply equations** still extract their value
from the shared full-model run rather than independently summing
per-ingredient contributions via the Feed Library (documented in each
equation's own `known_discrepancies`; see also "The Feed Library gap"
above).

**Diet optimizer** -- not started.

## Deployment (see README.md for full current details)

**Current, live, and confirmed working:** Render (`anllms-chat` service)
running `chat/server.py`, which routes model calls through a self-hosted
LiteLLM proxy on Cloud Run rather than calling `api.anthropic.com`
directly. Model selectable via the `ANLLMS_MODEL` env var; the
`gemini-flash` alias currently points at a deprecated underlying model
and needs a proxy-side fix (outside this repo) -- Mistral aliases are a
working temporary substitute.

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
