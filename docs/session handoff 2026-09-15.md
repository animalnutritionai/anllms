ANLLMS session handoff — Sept 15, 2026

WHAT WAS DONE THIS SESSION
- README.md Cloud Run -> Render correction (flagged open in the Sept 4
  handoff, now applied). Two references removed: the LiteLLM proxy's
  described platform and the stale, unverifiable Cloud Run URL. Rather
  than invent a Render URL that isn't recorded anywhere in this repo,
  the README now points to the `LITELLM_BASE_URL` env var on the
  `anllms-chat` Render service as the source of truth for the live
  value.
- Mineral/vitamin supply independence -- closed. This was the only
  remaining place in the codebase where a supply-side value was
  extracted from a shared full-model run instead of independently
  summed from the Feed Library, matching the pattern already used for
  RUP and microbial MP supply.
    - New module `feed_library/mineral_vitamin_supply.py` computes all
      14 mineral + 3 vitamin supply values from the real per-feed
      nasem_dairy pipeline (`_feed_data.py`'s build_complete_feed_data(),
      the same one RUP/microbial supply already use) -- no full
      nd.nasem() run required.
    - 10 minerals (Ca, P, Na, K, Cl, Co, Cu, Fe, Mn, Zn) are a direct
      sum of a per-feed Fd_abs*In column already produced inside
      nasem_dairy's calculate_feed_data(). 3 minerals (S, I, Se) and all
      3 vitamins have no absorption coefficient in the book at all --
      supply is the raw per-feed intake sum. Magnesium is the one
      genuine special case: Dt_acMg (the diet-level absorption
      coefficient) is inhibited by dietary K%, so Abs_MgIn needs the
      real nasem_dairy diet-level chain (Dt_MgIn, Dt_MgIn_min, Dt_KIn ->
      Dt_K -> Dt_acMg -> Abs_MgIn), not a per-feed sum. Every step calls
      a real nasem_dairy function -- nothing reimplemented.
    - Verified to rel_tol=1e-6 against a full nd.nasem() run on the
      lactating_cow_test demo scenario, for all 17 values.
    - All 17 *SupplyNASEM2021.calculate() methods rewired from
      model_output to a supply_data dict; their now-resolved
      known_discrepancies entries removed.
    - mineral_vitamin_water.py and requirements_report.py rewired to
      call the new module instead of passing model_output through.
    - Caught and fixed two stale doc-comments while in
      requirements_report.py: one still described this gap under "what
      this deliberately does not do yet" (removed, since it's done);
      one had a pre-existing "13 minerals" miscount (corrected to 14).
- docs/architecture.md updated: the Known Open Items entry for
  mineral/vitamin supply now reads "(closed)" with the fix described,
  and "The Feed Library gap (closed, for MP supply)" section heading
  now reads "(closed, for MP, mineral, and vitamin supply)".

FILES CHANGED (24 total)
  NEW:
    anllms/feed_library/mineral_vitamin_supply.py
    tests/test_mineral_vitamin_supply_independent.py
  MODIFIED:
    README.md                                  (Cloud Run -> Render)
    docs/architecture.md                       (open item closed,
                                                 section heading updated)
    anllms/scientific/minerals/calcium.py
    anllms/scientific/minerals/chlorine.py
    anllms/scientific/minerals/cobalt.py
    anllms/scientific/minerals/copper.py
    anllms/scientific/minerals/iodine.py
    anllms/scientific/minerals/iron.py
    anllms/scientific/minerals/magnesium.py
    anllms/scientific/minerals/manganese.py
    anllms/scientific/minerals/phosphorus.py
    anllms/scientific/minerals/potassium.py
    anllms/scientific/minerals/selenium.py
    anllms/scientific/minerals/sodium.py
    anllms/scientific/minerals/sulfur.py
    anllms/scientific/minerals/zinc.py
    anllms/scientific/vitamins/vitamin_a.py
    anllms/scientific/vitamins/vitamin_d.py
    anllms/scientific/vitamins/vitamin_e.py
    anllms/simulation/mineral_vitamin_water.py (model_output ->
                                                 supply_data throughout)
    anllms/simulation/requirements_report.py   (calls new module;
                                                 two stale doc-comments
                                                 fixed)
    tests/test_mineral_vitamin_supply.py       (rewritten for the new
                                                 supply_data interface)
    tests/test_mineral_vitamin_water_wiring.py (updated fixture call)

VALIDATION
- Full test suite: 212/213 passing. The 1 failure is the same
  pre-existing, unrelated test_magnesium.py wording assertion --
  untouched, already documented as a known issue since the Sept 4
  handoff.
- New independent-supply module checked against a real nd.nasem() run
  (lactating_cow_test), not invented numbers -- all 17 values within
  rel_tol=1e-6.
- Re-verified against a fresh codeload tarball pull of the live repo
  after upload: all 24 files present at the correct paths, byte-for-
  byte identical to what was delivered, and the full test suite re-run
  against that fresh pull matched the same 212/213 result.

WHAT'S STILL OPEN (per architecture.md)
1. solve_diet.py optimizer -- NOT YET STARTED. Design settled
   (scipy.optimize.differential_evolution, treating nd.nasem() as a
   black box, per published 2024 JAS precedent). diet_request.py's spec
   is built, tested, and has no placeholder fields. This is the agreed
   starting point for the next session. One design question flagged in
   diet_request.py for that build session to resolve, not resolved now:
   how a fixed known_dmi_kg (actual mode) should behave if candidate
   rations diverge materially from the ration it was measured against.
2. gemini-flash proxy alias fix -- Render-side config fix (not an
   anllms repo change); the alias currently points to a deprecated
   model version.
3. Repository separation -- not planned for at least two years; all
   decision-layer code stays within the anllms repo.

NEXT SESSION SUGGESTION
Start solve_diet.py -- both things it was waiting on (the DMI mode
decision, resolved Sept 4; mineral/vitamin supply independence, closed
this session) are done, and diet_request.py's spec is ready to build
against.
