"""
Diet solver -- searches candidate feed inclusion rates for a ration that
meets every NASEM (2021) requirement plus any extra constraints, and (if
requested) minimizes cost / maximizes IOFC.

LAYERING: part of anllms.decision (see anllms/decision/__init__.py).
Imports FROM anllms.decision.diet_request and anllms.decision.evaluate_diet
(both already in this package) and anllms.feed_library.ration. Nothing
outside anllms.decision may import this file (enforced by
tests/test_import_boundaries.py).

METHOD: scipy.optimize.differential_evolution (Storn & Price, 1997 --
see docs/citations.md Part B1), treating each candidate ration's full
nd.nasem() run as a BLACK BOX. No linearized approximation of any NASEM
equation is built here -- every candidate is scored by calling
evaluate_diet(), which itself wraps the real reference model, consistent
with this project's "wrap, don't reimplement" rule. This follows the
2024 J. Anim. Sci. abstract precedent (docs/citations.md Part B2).

CONSTRAINT HANDLING: differential_evolution has no built-in notion of
"NEL supply must meet NEL requirement". Every constraint here (default
NASEM requirement floors, plus anything in SolveRequest.nutrient_bounds)
is folded into ONE scalar objective via a penalty: a candidate that
falls short of a minimum or exceeds a maximum gets a large, FRACTIONAL
penalty added to its cost -- (shortfall / requirement), not an absolute
unit amount -- so nutrients on wildly different scales (mg/d selenium
vs. g/d MP) don't need a hand-picked scaling table. See _penalty().

SCOPE (v1, this session) -- WHAT IS NOT YET SUPPORTED, documented rather
than silently skipped:
  - NutrientBound.nutrient must be one of: "NEL", "MP", one of the 13
    mineral symbols, one of the 3 vitamin symbols (all via evaluate_diet,
    both absolute and relative bounds), or "NDF"/"ADF" (via
    Ration.to_diet(), absolute bounds only -- these two have no default
    NASEM requirement to be a percentage OF, so a relative bound on
    either raises. Any other nutrient name raises NotImplementedError
    naming it -- checked ONCE, before the optimizer starts, against one
    real ration built from the midpoint of every candidate feed's
    bounds, so this can't be silently swallowed by the per-candidate
    error handling described further below.
  - The ambiguity check NutrientBound's own docstring describes --
    override_default=False combined with a min BELOW the existing
    default requirement floor should raise -- IS enforced (see
    _check_ambiguous_override()), and checked at the same fail-fast
    canary point as nutrient resolvability, above. It is EXACT for
    relative bounds (min_pct_of_requirement < 100 is ambiguous
    regardless of the requirement's actual value, since both sides
    scale together). For an ABSOLUTE min_value bound it is only as
    exact as the canary ration: if dmi_mode="predict" lets a nutrient's
    requirement drift enough during the search that a bound which
    passed at the canary point becomes ambiguous for some later
    candidate, that candidate is scored as an evaluation error (see
    n_evaluation_errors below) rather than the whole solve raising.
    Narrow, documented gap rather than a silent one.
  - No automatic runtime scaling: each DE evaluation is a full
    nd.nasem() run. SolveOptions.maxiter/popsize bound the main search,
    but SolveOptions.polish (scipy's own default, True) can add MANY
    further evaluations on top -- confirmed by direct measurement this
    session: its local L-BFGS-B refinement needs ~5 full nd.nasem() runs
    per numerical-gradient estimate, and a feasibility-driven penalty
    objective commonly converges at a bounds corner, where that
    refinement can take a long time to settle. There is no guidance yet
    on sane maxiter/popsize values as candidate count grows. nfev on
    SolveResult reports the actual count so this is visible, not hidden.
  - A candidate ration on which evaluate_diet() itself raises or the
    underlying nd.nasem() run errors is treated as maximally infeasible
    (see _EVAL_FAILURE_PENALTY) rather than crashing the whole solve --
    SolveResult.n_evaluation_errors reports how often this happened, so
    a caller can tell a genuinely hard search space from a masked bug.

KNOWN LIMITATION carried from the 2024 J. Anim. Sci. precedent
(docs/citations.md Part B2): that abstract's own conclusion cautions
that a strategy is needed to close the gap between predicted and
observed individual-cow performance before using optimization to
auto-formulate diets. This codebase's milk yield is a caller-supplied
TARGET (MilkTarget), not a predicted response to diet composition (see
ObjectiveSpec's own docstring) -- solve_diet finds a diet that meets a
FIXED target at least cost, it does not predict how a cow will actually
perform on any given diet. Recorded so a result isn't presented as more
predictive than it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from anllms.decision.diet_request import NutrientBound, SolveRequest
from anllms.decision.evaluate_diet import DietEvaluation, NutrientEvaluation, evaluate_diet
from anllms.feed_library.ration import Ration

# Composition-only nutrients with no default NASEM requirement floor --
# sourced from Ration.to_diet() (real feed-library aggregation), not
# evaluate_diet(). Absolute bounds only; see module docstring.
_COMPOSITION_ONLY_FIELDS = {"NDF": "ndf_pct", "ADF": "adf_pct"}

# Added to the objective for a candidate that errors out entirely (e.g.
# nd.nasem() itself raises for a degenerate ration), so DE steers away
# from it without the whole solve crashing. Large enough to always lose
# to any evaluable candidate, feasible or not.
_EVAL_FAILURE_PENALTY = 1e12


@dataclass
class SolveOptions:
    """Tuning knobs for the underlying scipy optimizer. See module
    docstring's SCOPE section: there is no automatic scaling of these
    with candidate count yet."""

    maxiter: int = 100
    popsize: int = 15
    seed: int | None = None
    # scipy's own default (True): after the main search, run a local
    # L-BFGS-B refinement for a tighter answer. Confirmed by direct
    # measurement (this session) to cost many EXTRA full nd.nasem() runs
    # when it refines near a bounds corner -- each numerical gradient
    # estimate needs ~5 evaluations, and corner solutions are common for
    # a feasibility-driven penalty objective. Leave True for a real
    # solve; set False for a fast exploratory pass (this project's own
    # tests do).
    polish: bool = True
    # Weight applied to the summed FRACTIONAL constraint violation (see
    # _penalty()) before adding it to the cost-based objective. Large
    # relative to typical feed costs so any feasible candidate always
    # beats any infeasible one, regardless of cost.
    penalty_weight: float = 1e6


@dataclass
class ConstraintViolation:
    nutrient: str
    kind: str  # "min" or "max"
    required: float
    actual: float
    unit: str


@dataclass
class SolveResult:
    success: bool  # True iff the returned ration has zero ConstraintViolations
    ration: Ration
    evaluation: DietEvaluation
    objective_value: float  # feed cost, $/d ("feasibility_only" reports 0.0)
    iofc: float | None  # populated only for objective.kind == "maximize_iofc"
    violations: list[ConstraintViolation]
    scipy_message: str
    nfev: int  # number of full nd.nasem() runs performed
    n_evaluation_errors: int  # of those, how many raised (see module docstring)


def _lookup_requirement_linked(evaluation: DietEvaluation, nutrient: str) -> NutrientEvaluation | None:
    key = nutrient.upper()
    if key == "NEL":
        return evaluation.nel
    if key == "MP":
        return evaluation.mp
    for n in evaluation.minerals + evaluation.vitamins:
        if n.name.upper() == key:
            return n
    return None


def _default_bounds(evaluation: DietEvaluation) -> dict[str, tuple[float, float | None, str]]:
    """nutrient -> (min_required, max_required, unit) for every NASEM
    requirement solve_diet enforces by default. max is always None here
    -- NASEM defines a FLOOR, never a ceiling, for these."""
    out: dict[str, tuple[float, float | None, str]] = {}
    for n in [evaluation.nel, evaluation.mp] + evaluation.minerals + evaluation.vitamins:
        out[n.name.upper()] = (n.requirement, None, n.unit)
    return out


def _check_ambiguous_override(bound: NutrientBound, req_linked: NutrientEvaluation, min_v: float | None) -> None:
    """Raises if a non-override min sits BELOW the existing default NASEM
    requirement floor -- the exact ambiguity NutrientBound's own
    docstring describes. Only called when the nutrient HAS a default
    floor (req_linked is not None); a bound on a nutrient with no
    default has nothing to be ambiguous against.

    For a RELATIVE bound this is exact for every candidate: min_v is
    always requirement * pct/100, so min_v < requirement reduces to
    pct < 100 regardless of what the requirement itself happens to be.
    For an ABSOLUTE bound it's only as exact as the evaluation passed
    in -- see solve_diet()'s canary-check comment for the one known gap
    this leaves (predict-mode DMI drift between the canary ration and a
    later candidate)."""
    if bound.override_default or min_v is None:
        return
    if min_v < req_linked.requirement:
        raise ValueError(
            f"NutrientBound({bound.nutrient!r}): min ({min_v:.4g} {req_linked.unit}) "
            f"is below the existing default NASEM requirement floor "
            f"({req_linked.requirement:.4g} {req_linked.unit}) for this ration, but "
            f"override_default=False. This is ambiguous: does the lower min REPLACE "
            f"the default (in which case set override_default=True), or did you mean "
            f"an additional floor at least as high as the default (in which case raise "
            f"min_value / min_pct_of_requirement to 100 or above)?"
        )


def _resolve_bound(
    bound: NutrientBound,
    evaluation: DietEvaluation,
    ration: Ration,
    baseline_requirements: dict[str, float],
) -> tuple[float | None, float | None, str]:
    """One NutrientBound -> (min, max, unit) in absolute units, for THIS
    candidate. Relative (pct_of_requirement) bounds are converted here,
    using either this candidate's own requirement (per_candidate) or the
    precomputed baseline_requirements (baseline_locked) -- see
    SolveRequest.relative_floor_basis and diet_request's
    RELATIVE_FLOOR_BASIS_EXPLANATION. Also enforces the override-ambiguity
    check described in NutrientBound's docstring; see
    _check_ambiguous_override()."""
    key = bound.nutrient.upper()
    req_linked = _lookup_requirement_linked(evaluation, bound.nutrient)

    if bound.is_relative():
        if req_linked is None:
            raise NotImplementedError(
                f"NutrientBound({bound.nutrient!r}): a relative "
                f"(pct_of_requirement) bound needs a default NASEM "
                f"requirement to be a percentage of, but {bound.nutrient!r} "
                f"has none in this codebase (only NEL, MP, the 13 minerals, "
                f"and the 3 vitamins do). Use an absolute min_value/"
                f"max_value bound instead."
            )
        requirement = baseline_requirements.get(key, req_linked.requirement)
        min_v = requirement * bound.min_pct_of_requirement / 100.0 if bound.min_pct_of_requirement is not None else None
        max_v = requirement * bound.max_pct_of_requirement / 100.0 if bound.max_pct_of_requirement is not None else None
        _check_ambiguous_override(bound, req_linked, min_v)
        return min_v, max_v, req_linked.unit

    if req_linked is not None:
        _check_ambiguous_override(bound, req_linked, bound.min_value)
        return bound.min_value, bound.max_value, req_linked.unit

    field_name = _COMPOSITION_ONLY_FIELDS.get(key)
    if field_name is not None:
        return bound.min_value, bound.max_value, bound.unit or "% of DM"

    raise NotImplementedError(
        f"NutrientBound({bound.nutrient!r}): not a nutrient solve_diet "
        f"can currently source a value for. Supported: NEL, MP, the 13 "
        f"mineral symbols, the 3 vitamin symbols (via evaluate_diet), or "
        f"NDF/ADF (via Ration.to_diet()). See solve_diet.py's module "
        f"docstring SCOPE section for why others aren't wired up yet."
    )


def _effective_min_max(
    request: SolveRequest,
    evaluation: DietEvaluation,
    ration: Ration,
    baseline_requirements: dict[str, float],
) -> dict[str, tuple[float | None, float | None, str]]:
    """Every nutrient this candidate is constrained on -> (min, max, unit),
    combining NASEM default floors with SolveRequest.nutrient_bounds.
    override_default=True REPLACES a default floor; override_default=False
    (or a nutrient with no default) ADDS alongside it (see NutrientBound
    docstring, and this module's SCOPE note on the not-yet-enforced
    ambiguity check)."""
    effective = {k: v for k, v in _default_bounds(evaluation).items()}

    for bound in request.nutrient_bounds:
        key = bound.nutrient.upper()
        min_v, max_v, unit = _resolve_bound(bound, evaluation, ration, baseline_requirements)

        if bound.override_default or key not in effective:
            effective[key] = (min_v, max_v, unit)
        else:
            existing_min, existing_max, existing_unit = effective[key]
            combined_min = max(v for v in (existing_min, min_v) if v is not None) if (existing_min is not None or min_v is not None) else None
            combined_max = min(v for v in (existing_max, max_v) if v is not None) if (existing_max is not None or max_v is not None) else None
            effective[key] = (combined_min, combined_max, existing_unit)

    return effective


def _penalty(effective: dict[str, tuple[float | None, float | None, str]], evaluation: DietEvaluation, ration: Ration) -> tuple[float, list[ConstraintViolation]]:
    """Sum of fractional constraint violations across every entry in
    `effective`, plus the ConstraintViolation list for reporting. A
    candidate that satisfies everything returns (0.0, [])."""
    total = 0.0
    violations: list[ConstraintViolation] = []

    for key, (min_v, max_v, unit) in effective.items():
        req_linked = _lookup_requirement_linked(evaluation, key)
        if req_linked is not None:
            actual = req_linked.supply
        else:
            field_name = _COMPOSITION_ONLY_FIELDS[key]
            actual = getattr(ration.to_diet(), field_name)

        if actual is None:
            continue  # not_available -- nothing to penalize against (see evaluate_diet)

        if min_v is not None and actual < min_v:
            frac = (min_v - actual) / min_v if min_v else (min_v - actual)
            total += frac
            violations.append(ConstraintViolation(key, "min", min_v, actual, unit))
        if max_v is not None and actual > max_v:
            frac = (actual - max_v) / max_v if max_v else (actual - max_v)
            total += frac
            violations.append(ConstraintViolation(key, "max", max_v, actual, unit))

    return total, violations


def solve_diet(request: SolveRequest, options: SolveOptions | None = None) -> SolveResult:
    """
    Search request.candidate_feeds' inclusion rates for a ration meeting
    every default NASEM requirement plus request.nutrient_bounds, and (if
    request.objective needs it) minimizing feed cost. See module
    docstring for method, constraint handling, and current scope limits.
    """
    from scipy.optimize import differential_evolution

    options = options or SolveOptions()

    missing_feeds = request.missing_feed_names()
    if missing_feeds:
        raise ValueError(f"candidate_feeds not found in the real feed library: {missing_feeds}")

    missing_bounds = request.missing_finite_bounds()
    if missing_bounds:
        raise ValueError(
            f"solve_diet needs a finite upper bound for every candidate "
            f"feed to search over. No IngredientBound.max_kg_dm_per_day "
            f"and no SolveRequest.default_max_kg_dm_per_day is set for: "
            f"{missing_bounds}. Supply one or the other."
        )

    missing_prices = request.missing_prices()
    if missing_prices:
        raise ValueError(f"objective {request.objective.kind!r} needs a price for: {missing_prices}")

    bounds = [request.effective_ingredient_bounds(f) for f in request.candidate_feeds]

    baseline_requirements: dict[str, float] = {}
    # (populated below, before the canary check, so a relative bound
    # against a baseline can also be validated up front)
    if request.relative_floor_basis == "baseline_locked":
        baseline_eval = evaluate_diet(
            request.animal, request.milk, request.baseline_ration,
            dmi_mode=request.dmi_mode, known_dmi_kg=request.known_dmi_kg,
        )
        baseline_requirements = {
            n.name.upper(): n.requirement
            for n in [baseline_eval.nel, baseline_eval.mp] + baseline_eval.minerals + baseline_eval.vitamins
        }

    # Fail-fast validation: resolve every nutrient_bounds entry once,
    # against one real ration, BEFORE starting the optimizer. Without
    # this, a NotImplementedError from an unsupported nutrient (or a
    # relative bound on one with no default requirement) would be
    # swallowed by the objective()'s own except-Exception below -- which
    # exists to catch genuine per-candidate nd.nasem() failures, not
    # spec-level mistakes -- and DE would silently run its full budget
    # treating every candidate as infeasible instead of raising.
    canary_ration = Ration()
    for name, (lo, hi) in zip(request.candidate_feeds, bounds):
        canary_ration.add(name, (lo + hi) / 2.0)
    canary_eval = evaluate_diet(
        request.animal, request.milk, canary_ration,
        dmi_mode=request.dmi_mode, known_dmi_kg=request.known_dmi_kg,
    )
    _effective_min_max(request, canary_eval, canary_ration, baseline_requirements)

    n_errors = 0

    def objective(x) -> float:
        nonlocal n_errors
        ration = Ration()
        for name, kg in zip(request.candidate_feeds, x):
            ration.add(name, float(kg))

        try:
            evaluation = evaluate_diet(
                request.animal, request.milk, ration,
                dmi_mode=request.dmi_mode, known_dmi_kg=request.known_dmi_kg,
            )
            effective = _effective_min_max(request, evaluation, ration, baseline_requirements)
            penalty, _ = _penalty(effective, evaluation, ration)
        except Exception:
            n_errors += 1
            return _EVAL_FAILURE_PENALTY

        cost = sum(request.objective.feed_prices.get(name, 0.0) * kg for name, kg in zip(request.candidate_feeds, x))
        base = cost if request.objective.needs_prices() else 0.0
        return base + penalty * options.penalty_weight

    result = differential_evolution(
        objective, bounds, maxiter=options.maxiter, popsize=options.popsize,
        seed=options.seed, polish=options.polish,
    )

    ration = Ration()
    for name, kg in zip(request.candidate_feeds, result.x):
        ration.add(name, float(kg))

    evaluation = evaluate_diet(
        request.animal, request.milk, ration,
        dmi_mode=request.dmi_mode, known_dmi_kg=request.known_dmi_kg,
    )
    effective = _effective_min_max(request, evaluation, ration, baseline_requirements)
    _, violations = _penalty(effective, evaluation, ration)

    cost = sum(request.objective.feed_prices.get(name, 0.0) * kg for name, kg in zip(request.candidate_feeds, result.x))
    objective_value = cost if request.objective.needs_prices() else 0.0
    iofc = None
    if request.objective.kind == "maximize_iofc":
        iofc = request.objective.milk_price_per_kg * request.milk.yield_kg - cost

    return SolveResult(
        success=(len(violations) == 0),
        ration=ration,
        evaluation=evaluation,
        objective_value=objective_value,
        iofc=iofc,
        violations=violations,
        scipy_message=result.message,
        nfev=result.nfev,
        n_evaluation_errors=n_errors,
    )
