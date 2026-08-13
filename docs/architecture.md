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

- **Magnesium gestation equation number: RESOLVED by structural
  cross-reference, not yet by a direct paginated-book read**
  (`scientific/minerals/magnesium.py`, `MagnesiumGestationNASEM2021`).
  The source document has a text-extraction gap around this equation
  (two consecutive "(Equation 20-402)" labels with no formula text
  between them). The FORMULA was already confirmed correct against real
  fixture test data (including its step-function behavior: zero before
  day 190 of gestation, a fixed BW-scaled amount after). The citation
  number has now been resolved too: cross-referencing the analogous
  Calcium/Phosphorus sections (same missing-formula pattern, zero
  duplicate equation numbers) against the reference software's function
  order (Ur_Mg_m -> Fe_Mg_m -> An_Mg_m -> An_Mg_g -> An_Mg_y -> An_Mg_l
  -> An_Mg_req) gives growth = Eq. 20-401, gestation = Eq. 20-402.
  `magnesium.py` and its tests were updated accordingly. This is a
  high-confidence reconstruction, not a direct paginated-book read --
  a paginated-copy spot-check would still be the gold-standard
  confirmation if one becomes available.

## Recommended next step

Mineral and vitamin SUPPLY is independently cited for all 13 minerals
and 3 vitamins. Gestation MP and NEL requirement are now independently
cited (Eq. 20-238/20-239 for MP, Eq. 20-236/20-237 for NEL) -- both
were closed as of this update.

Remaining known gap, explicitly deferred as its own future task per
project decision: FRAME/BODY RESERVE GROWTH requirement components
(Frm/Rsrv terms for both MP and NEL) still come from the reference
model directly, not independently cited. Unlike gestation, their
equation numbers were not found in the same requirements-chapter
sections of the book searched so far -- they likely belong to NASEM's
separate, larger Growth chapter with its own terminology (empty body
gain, retained energy, etc.), which hasn't been mapped in this codebase
yet. This is zero-impact for a standard mature cow with no explicit
frame/reserve gain target, but affects any scenario modeling active
heifer growth or deliberate body condition change.

Other remaining gaps: mineral/vitamin supply equations still extract
their value from the shared full-model run rather than independently
summing per-ingredient contributions (documented in each equation's
own known_discrepancies, same scope decision as RUP-derived MP supply).
The live chat interface has been run successfully via GitHub Codespaces
but not yet stress-tested with varied real conversations. A diet
optimizer has not been started.

## Session update: base-diet fallback, serialization fix, chat logging

**Base-diet fallback for chat queries with no formulated diet.**
`Ration.guelph_base_diet()` (in `feed_library/ration.py`) now provides
a fallback diet -- nasem_dairy's own built-in demo ration
(`nd.demo("lactating_cow_test")`: alfalfa meal, canola meal, corn
silage typical, corn grain HM coarse grind, ~24.5 kg DM/d), NOT a
NASEM book example. `chat/tools.py`'s `calculate_lactating_cow_requirements`
uses this automatically when `ration_items` is omitted, and inserts an
explicit warning into the report (and the system prompt now instructs
Claude to relay it) so a placeholder-diet result is never presented as
if it reflected the user's actual ration.

**Serialization gap found and fixed.** Despite an earlier note that a
`blocks_to_dicts()` helper had already addressed Anthropic SDK content
blocks being stored raw in message history, no such helper existed in
`main` as of this session -- `server.py` was passing raw SDK objects
(pydantic models) directly to `jsonify()`, which would raise a
`TypeError` on any turn involving a tool call. This is now fixed:
`chat/logging_utils.py` provides `blocks_to_dicts()`, used both to
serialize `messages` before `jsonify()` and for the new chat logger
below. **Not yet independently re-verified against a live run with a
real API key** -- next session should confirm the fix resolves a real
tool-use turn, not just that the code looks correct on inspection.

**Chat transcript logging, test phase only.** Opt-in via
`ANLLMS_CHAT_LOG=1` env var; writes one timestamped `.jsonl` file per
server run to `chat/logs/`, one JSON line per turn. **Current policy:
these logs ARE committed to the repo** (see `chat/logs/README.md`),
by explicit project decision, because test sessions are verified free
of real farm/animal data before they're run. This policy does NOT
carry over to commercial use -- before real customer data is ever
logged, this needs a full redesign: no git commit, a proper backend
store (DB or managed logging service), user disclosure/consent,
a retention limit, access control and encryption at rest, and a legal
review of what's being collected. Noted here as a forward-looking item,
not built yet, since there's no real backend or user base to design
concretely against.


---

**File: `docs/architecture.md`**



## Session update: accessible chat testing via Codespaces (screen-reader workflow)

**Problem.** The GitHub Codespaces IDE (editor UI + embedded terminal) is
difficult to navigate with JAWS (PC) and VoiceOver (iPhone) -- output is
often hard to read and the terminal is hard to navigate by screen reader.
Render and Replit were also tried and found inadequate for the same
underlying reason: dense, dynamically-updating dashboards are harder for
screen readers than simpler, page-based UIs. Running a local server was
ruled out (unwilling to run project code/dependencies on a personal
laptop). Goal: reach the existing plain `chat/static/index.html` page
directly, bypassing the IDE entirely, using Codespaces' built-in port
forwarding.

**Attempt 1: `.devcontainer/devcontainer.json` with a backgrounded
`postStartCommand`** (`pip install -e '.[chat]' && python chat/server.py &`),
intended to auto-start the server with zero terminal interaction on every
Codespace resume. Result: the forwarded chat page loaded but was
completely blank (not a Codespaces "port not running" error, and a
nonexistent path returned no error page either -- suggesting Flask never
actually bound to the port). Likely cause: backgrounding the command with
`&` meant Flask's own startup output had nowhere to go, so neither a
person nor Codespaces' automatic port-detection (which watches terminal
output for a `http://localhost:PORT` line) could see whether `pip install`
or the server itself succeeded or failed. This `.devcontainer` config was
not kept in the repo pending further debugging (redirecting output to a
log file was proposed as the fix, not yet tried).

**Attempt 2 (current working approach): manual terminal launch.**
`server.py` already binds to `host="0.0.0.0"` (required for Codespaces
port forwarding to reach it; `localhost`-only binding would not work).
With `ANTHROPIC_API_KEY` set as a repo-level Codespace secret (auto-injected,
no manual `export` needed), the commands are:

```bash
pip install -e ".[chat]"
python -m chat.server
```

This is the currently-active testing path: the forwarded port serves
`chat/static/index.html` directly, bypassing the Codespaces IDE. It has
been run successfully at least once (see "Recommended next step" above)
but has not yet been stress-tested with varied real conversations, and
the `blocks_to_dicts()` serialization fix has not yet been independently
re-verified against a live tool-use turn with a real API key.

*(Note: this section's code block was left unclosed in a prior save of
this file, cutting the document off mid-command. Closed out here with
no new claims added beyond what was already stated elsewhere in this
document.)*

## Session update: PythonAnywhere deployment path prepared -- NOT YET SET UP OR TESTED

**TO DO, next session: actually walk through this and confirm it works.**
Nothing below has been run yet -- it's a prepared path, not a working
deployment.

**What was added.** `deploy/README.md` (step-by-step PythonAnywhere setup
walkthrough) and `deploy/pythonanywhere_wsgi_template.py` (the WSGI entry
point PythonAnywhere needs to import `chat/server.py`'s existing `app`
object). The goal: a permanent `yourusername.pythonanywhere.com` URL
reachable directly from Safari, replacing the Codespaces
start-terminal/kill-terminal cycle entirely for day-to-day chat testing.

**Why this should work, unverified.** `chat/server.py`'s `app = Flask(...)`
is already defined at module level, with `app.run(...)` guarded behind
`if __name__ == "__main__"` -- so importing `chat.server` without running
it (as a WSGI server does) should just work, without code changes.
`api.anthropic.com` was directly confirmed present on PythonAnywhere's
current free-account allowlist (checked against their published
allowlist page), so the free tier -- which is what's already set up, no
card required -- should be able to reach the Anthropic API without an
upgrade. Both of these are reasoning from how the code and the allowlist
currently look, not confirmation that the actual deployment works.

**What's still unverified / what to check next session:**
- Whether the `mkvirtualenv` + `pip install -e ".[chat]"` steps actually
  succeed on PythonAnywhere's free-tier CPU/disk limits.
- Whether the WSGI file, once edited with the real repo path and API
  key, actually serves `chat/static/index.html` and completes a live
  tool-use turn against `api.anthropic.com` -- the same
  `blocks_to_dicts()` serialization fix noted above as unverified on
  Codespaces is equally unverified here, since it's the same code path.
- Whether PythonAnywhere's free-tier daily CPU-second allowance is
  sufficient for realistic test-session usage, or whether it becomes a
  practical limitation.
- Whether `chat/logs/publish_transcript.sh` runs cleanly from a
  PythonAnywhere Bash console (git identity/credentials may need setup
  there separately from Codespaces).

Codespaces remains the last **confirmed-working** testing path until
this one is actually walked through and verified.

