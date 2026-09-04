ANLLMS session handoff — Sept 4, 2026

WHAT WAS DONE THIS SESSION
- Resolved the DMI actual-vs-predicted mode decision (the scheduled
  focus per the Aug 30 handoff). build_requirements_report() and
  evaluate_diet() both now accept dmi_mode ("predict" | "actual") and
  known_dmi_kg. "actual" mode skips DMI prediction entirely and uses a
  caller-supplied value directly, mirroring the reference software's own
  DMIn_eqn == 0 mode -- via a new citation-backed equation object,
  MeasuredDMINASEM2021, rather than an ad hoc bypass.
- Wired dmi_mode/known_dmi_kg through the chat tool layer
  (calculate_lactating_cow_requirements and evaluate_diet tool schemas
  in chat/tools.py), with tool descriptions instructing the LLM to ask
  the user whether they already know the cow's actual DMI before
  defaulting to prediction. Default stays "predict" -- no existing
  caller breaks.
- evaluate_diet()'s DMI-mismatch warning is now mode-aware: "predict"
  mode frames a mismatch as a modeling subtlety (predicted vs. ration
  total); "actual" mode frames it as a data-entry question (ration
  doesn't total to the measured DMI supplied). These should never be
  worded the same way, since they mean different things.
- Updated diet_request.py's docstring/comments: dmi_mode/known_dmi_kg
  are no longer placeholders -- the decision they were waiting on is
  resolved. One remaining open question (fixed measured DMI going stale
  if a future solver explores very different candidate rations) is
  explicitly flagged there for solve_diet's own build session to
  resolve, not resolved now.
- Corrected a memory error: the LiteLLM proxy runs on Render
  (litellm:main-latest), NOT Cloud Run as memory previously stated.
  Confirmed via session_handoff_2026-08-30.md and architecture.md.
  README.md still needs this correction applied -- flagged as an open
  doc task, not yet done.

FILES CHANGED (9 total)
  NEW:
    anllms/scientific/energy/dmi_measured.py
    tests/test_dmi_measured.py
  MODIFIED:
    anllms/simulation/requirements_report.py  (dmi_mode param added)
    anllms/decision/evaluate_diet.py          (dmi_mode param added,
                                                mode-aware mismatch
                                                warnings, dmi_mode field
                                                added to DietEvaluation)
    anllms/decision/diet_request.py           (docstring/comments only
                                                -- no code change; the
                                                fields already validated
                                                correctly)
    chat/tools.py                             (both tool schemas +
                                                dispatch methods)
    tests/test_requirements_report.py         (+5 tests)
    tests/test_evaluate_diet.py               (+4 tests)
    tests/test_chat_tools.py                  (+6 tests)

VALIDATION
- Full test suite: 213/214 passing (up from 195/196). The 1 failure is
  the same pre-existing, unrelated test_magnesium.py wording assertion
  -- untouched, already documented as a known issue.
- Import boundary test (test_import_boundaries.py) still passes --
  decision/ layer separation intact after these changes.
- Re-verified against a fresh `git clone` (not just a tarball pull) of
  the live repo after upload, including a `git diff --stat` against the
  pre-session commit (6ed2afd, "hand-off" from Sept 2) to confirm ONLY
  the 9 intended files changed and nothing else was accidentally
  touched or deleted.

FILE-UPLOAD PROCESS NOTE (worth reading before the next file-delivery-
heavy session -- see architecture.md's new "Recurring workflow risk"
section for the full writeup)
This session's file handoff hit two real naming failures before landing
correctly: (1) the file-sharing UI's display name strips underscores for
readability, and when that display name got used as the actual saved
filename, files landed with spaces instead of underscores; (2) a
re-upload whose filename didn't exactly match the file it was meant to
replace (extra trailing whitespace) caused git to create a new sibling
file instead of overwriting -- leaving stale old content live at the
correct path while new content sat under a wrongly-named file alongside
it. Fix that worked: state each file's exact intended repo path in its
own standalone code block immediately before presenting that file (one
path-then-file pair per file, not a batched list). This is now standard
practice going forward (also saved as a standing memory instruction).
Verification discipline that caught both failures: re-pulling the repo
fresh via `git clone` (not just the codeload tarball) after any upload,
diffing each file's exact content against what was generated, and
running `git diff --stat` against the pre-session commit to catch
anything unintended.

WHAT'S STILL OPEN (per architecture.md)
1. solve_diet.py optimizer -- NOT YET STARTED. Design settled
   (scipy.optimize.differential_evolution, treating nd.nasem() as a
   black box, per published 2024 JAS precedent). diet_request.py spec
   is built, tested, and no longer has placeholder DMI fields. This is
   the natural next piece of work now that its stated blocker (DMI mode)
   is resolved. One design question to resolve when building it: how a
   fixed known_dmi_kg (actual mode) should behave if candidate rations
   diverge materially from the ration it was measured against.
2. Mineral/vitamin supply independence -- still the only remaining
   place that extracts values from a full model run instead of
   independently summing per-ingredient contributions (RUP and
   microbial supply already closed this gap in an earlier session).
3. gemini-flash proxy alias fix -- Render-side config fix (not an
   anllms repo change); the alias currently points to a deprecated
   model version.
4. README.md update -- needs the Cloud Run -> Render correction
   (architecture.md already has this correct; README.md doesn't yet).
   Also a good time to batch in any other README-vs-architecture.md
   drift found this session.
5. Repository separation -- not planned for at least two years; all
   decision-layer code stays within the anllms repo.

NEXT SESSION SUGGESTION
Recommend starting solve_diet.py, since architecture.md's stated
blocker (the DMI mode decision) is now resolved and diet_request.py's
spec is ready to build against. The README.md Cloud Run correction is a
quick, low-risk task that could be batched in at the start or end of
that session rather than needing its own session. Open to other
priorities if preferred.
