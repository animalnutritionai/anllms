"""
Decision layer -- diet evaluation, solving, and sensitivity analysis.

LAYERING RULE (enforced by tests/test_import_boundaries.py):
Files in this package may import from anllms.knowledge, anllms.scientific,
anllms.feed_library, and anllms.simulation. Nothing in those four
packages may ever import from anllms.decision, in either direction of
this project's growth. This keeps the citation/calculation engine
(which end users' scientific trust depends on) permanently unaware of,
and unaffected by, whatever gets built here -- including anything that
turns out to be wrong, half-finished, or later thrown away.

Contents (see docs/architecture.md for current status of each):
  evaluate_diet.py   <- given a real ration, does it meet requirements?
                         (built first: no new optimization engine needed,
                         wraps simulation/requirements_report.py directly)
  solve_diet.py       <- NOT YET BUILT. Least-cost / IOFC-maximizing diet
                         formulation, planned to call nd.nasem() directly
                         per candidate ration rather than a linearized
                         approximation (see Aug 2026 architecture
                         discussion).
  sensitivity.py      <- NOT YET BUILT. Sweeps one input across a range,
                         re-running evaluate_diet/solve_diet at each
                         value -- no new optimization logic, pure
                         orchestration over the other two.
"""
