# Session Handoff — Aug 30, 2026

## Recap: what this session built

Started from the project's standing "CURRENT STATUS" instructions box.
Pulled both repos fresh, confirmed `docs/architecture.md` was current
(evaluate_diet not yet built, diet optimizer "not started"), then did
four things in order:

1. **New `anllms/decision/` package** — a permanently separate layer
   (no repo split planned for 2+ years) for diet evaluation/solving,
   isolated from the citation/calculation engine by a ONE-WAY import
   boundary, machine-enforced by `tests/test_import_boundaries.py`
   (fails the suite if `knowledge/`, `scientific/`, `feed_library/`, or
   `simulation/` ever imports from `decision/`).

2. **`evaluate_diet.py` — BUILT, tested, wired into chat.** Given a
   real ration, reports adequacy against every NASEM requirement.
   Requires a real ration (no placeholder fallback — that's reserved
   for the general/reference chat tool only). Flags when a ration's
   own total kg DM/d diverges >10% from the model's *predicted* DMI.
   Output is specialist-scannable: % of requirement met + a
   deficient/meets_or_exceeds status per nutrient, deficient ones
   surfaced first. New chat tool `evaluate_diet`, distinct from
   `calculate_lactating_cow_requirements` (kept for the no-ration
   general case).

3. **`diet_request.py` — the objective/constraint spec for the
   not-yet-built solver.** `ObjectiveSpec` (`feasibility_only`,
   `least_cost`, `maximize_iofc`), `IngredientBound`, `NutrientBound`,
   `SolveRequest`, all validated and tested. Engine choice for
   `solve_diet` itself was also settled this session (see below) but
   not yet built.

4. **`docs/architecture.md` regenerated** to fold all of this in, plus
   a real finding from testing `evaluate_diet` against
   `nasem_dairy`'s own demo scenario (see DMI item below), plus a
   Render deploy diagnosis (see below).

Full test suite: **188/189 passing** (162/163 at session start), same
one pre-existing unrelated `test_magnesium.py` wording gap as always.

**Files delivered for upload this session** (confirm these were
actually applied via GitHub's web editor before starting next time):
`anllms/decision/__init__.py`, `tests/test_import_boundaries.py`,
`anllms/decision/evaluate_diet.py`, `tests/test_evaluate_diet.py`,
`anllms/decision/diet_request.py`, `tests/test_diet_request.py`,
`chat/tools.py` (replaced), `chat/server.py` (replaced),
`docs/architecture.md` (replaced).

## Start next session here: the DMI actual-vs-predicted decision

This is the explicit next task, agreed this session, not just a
suggestion. Short version: `evaluate_diet` currently ALWAYS predicts
DMI (Eq. 2-1/2-2), even when a specialist already knows the client
cow's actual measured intake. Testing against `nasem_dairy`'s own demo
scenario showed the reference software itself supports an "actual DMI,
skip prediction" mode (`DMIn_eqn=0`) that our code has no equivalent
of. Per discussion, the specialist will know actual DMI ~95% of the
time and should be able to use it directly; prediction should be the
fallback, not the default.

This needs a real design pass, not a quick patch — it has to be
threaded consistently through `calculate_lactating_cow_requirements`,
`evaluate_diet`, and every candidate-ration call `solve_diet` will
eventually make, plus a clear way of telling the end user which mode
was used for any given number. `diet_request.py` already has
placeholder `dmi_mode`/`known_dmi_kg` fields for this, unwired to any
logic yet. Full detail in `docs/architecture.md`'s "Known Open Items"
section under this same heading.

## After that: solve_diet itself

Design already settled, ready to build once DMI mode is resolved
(the optimizer will need to know which mode it's running candidate
rations in):
- Black-box global optimizer (`scipy.optimize.differential_evolution`)
  calling the real `nd.nasem()` per candidate ration — not a
  linearized approximation, matching published precedent (2024 J.
  Animal Science) and this project's "wrap, don't reimplement"
  principle.
- Consumes `diet_request.SolveRequest`.
- `maximize_iofc` is mathematically identical to `least_cost` today
  (milk yield held fixed) — documented in `diet_request.py`'s
  docstring so this doesn't get relitigated or silently "fixed" by a
  future session without a deliberate decision to add a real
  production-response function.
- `sweep_parameter` (sensitivity/what-if/scenario questions) and the
  actual `SolveResult`/infeasibility-reporting shape are both
  deliberately not yet designed — natural follow-ups once `solve_diet`
  itself exists.

## Deployment status: healthy, no action needed

Diagnosed a Render failure-notification email this session — it
referred to an Aug 28 deploy (two days stale), root-caused via Render
MCP logs to the same vitamin-filename bug already documented and
already fixed same-day by a follow-up commit. Current live deployment
is healthy. Also corrected a doc inaccuracy while in there: the
LiteLLM proxy runs on Render (`litellm:main-latest` service), not
Cloud Run as previously assumed. Still open, unrelated to this
session: `gemini-flash` alias on the proxy points to a deprecated
model; Mistral aliases remain the working substitute.

## Reminder for next session's opening

Per the standing protocol: pull both repos fresh via
`codeload.github.com`, read `README.md` and `docs/architecture.md`
before touching code, confirm the files above actually made it into
the repo, then start on the DMI mode decision.
