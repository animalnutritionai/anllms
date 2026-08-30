"""
Diet solve request spec -- the objective + constraint shape solve_diet
(not yet built) will consume. Designed and validated ahead of the
optimizer itself so the engine work (scheduled after the DMI
actual-vs-predicted decision, see docs/architecture.md's Known Open
Items) can be built directly against a settled contract, rather than
co-designing the spec and the engine at the same time.

LAYERING: part of anllms.decision (see anllms/decision/__init__.py).
Imports FROM anllms.feed_library only, to validate ingredient names
against the real feed library the same way Ration does. Nothing in
knowledge/, scientific/, feed_library/, or simulation/ may import this
file (enforced by tests/test_import_boundaries.py).

DESIGN PRINCIPLE: every NASEM requirement (NEL, MP, all 13 minerals,
all 3 vitamins) is a DEFAULT hard constraint (supply >= requirement)
that solve_diet will apply automatically -- nothing here needs to
restate them. This module only covers what a caller ADDS on top of
that default floor: ingredient inclusion limits, extra/overriding
nutrient bounds (e.g. an NDF ceiling, which has no NASEM requirement
equation of its own), and the objective itself.

WHAT THIS DELIBERATELY DOES NOT COVER YET:
  - Ratio-style constraints (e.g. forage:concentrate) -- flagged as a
    future extension, not built now, to keep this pass scoped to what
    the discussed use cases actually need.
  - How infeasibility gets reported back (SolveResult / feasibility
    report shape) -- that's solve_diet's own design question, once the
    engine itself is being built, not this request spec's job.
  - DMI mode (actual vs. predicted). dmi_mode/known_dmi_kg below are
    PLACEHOLDER fields only -- unused by anything today, included so
    this spec doesn't need to be reshaped once tomorrow's dedicated DMI
    session lands. Do not wire logic to them yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from anllms.simulation.animal_state import AnimalState, MilkTarget

ObjectiveKind = Literal["feasibility_only", "least_cost", "maximize_iofc"]

_OBJECTIVE_KINDS: set[str] = {"feasibility_only", "least_cost", "maximize_iofc"}
_PRICE_DEPENDENT_KINDS: set[str] = {"least_cost", "maximize_iofc"}


@dataclass
class ObjectiveSpec:
    """
    What solve_diet should optimize for.

    feasibility_only: no cost/price data needed -- find any diet meeting
        every constraint (the "just formulate something that works" case,
        useful when a specialist doesn't have feed prices on hand yet).
    least_cost: minimize sum(feed_prices[i] * kg_i) subject to every
        constraint. Requires a price for every candidate feed.
    maximize_iofc: milk_price_per_kg * milk.yield_kg - feed cost.
        IMPORTANT, documented here so it isn't silently lost: with milk
        yield held fixed (which is how this codebase's requirement
        equations work -- they don't predict a production RESPONSE to
        diet quality), this is mathematically identical to least_cost;
        revenue is constant, so minimizing cost maximizes profit. Kept
        as a separate labeled kind for reporting clarity (a specialist
        asking to "maximize IOFC" should see IOFC in the result, not
        just a cost number), not because the underlying math differs
        today. A genuine production-response version would need its own
        citation-backed milk-response function -- a deliberate, separate
        future addition, not something to fold in here silently.
    """

    kind: ObjectiveKind
    milk_price_per_kg: float | None = None
    feed_prices: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in _OBJECTIVE_KINDS:
            raise ValueError(f"Unknown objective kind: {self.kind!r}. Must be one of {_OBJECTIVE_KINDS}")
        if self.kind == "maximize_iofc" and self.milk_price_per_kg is None:
            raise ValueError("maximize_iofc requires milk_price_per_kg")
        for name, price in self.feed_prices.items():
            if price < 0:
                raise ValueError(f"Negative feed price for {name!r}: {price}")

    def needs_prices(self) -> bool:
        return self.kind in _PRICE_DEPENDENT_KINDS


@dataclass
class IngredientBound:
    """Optional inclusion-rate limit for one candidate feed. Feeds with
    no IngredientBound default to [0, unbounded] in solve_diet -- this
    spec does not impose a physically-realistic default ceiling; that's
    the caller's responsibility (or a future diet-formulation-sanity
    layer's, not this one's)."""

    feed_name: str
    min_kg_dm_per_day: float | None = None
    max_kg_dm_per_day: float | None = None

    def __post_init__(self) -> None:
        if self.min_kg_dm_per_day is not None and self.min_kg_dm_per_day < 0:
            raise ValueError(f"min_kg_dm_per_day cannot be negative: {self.min_kg_dm_per_day}")
        if (
            self.min_kg_dm_per_day is not None
            and self.max_kg_dm_per_day is not None
            and self.min_kg_dm_per_day > self.max_kg_dm_per_day
        ):
            raise ValueError(
                f"{self.feed_name!r}: min_kg_dm_per_day ({self.min_kg_dm_per_day}) "
                f"exceeds max_kg_dm_per_day ({self.max_kg_dm_per_day})"
            )


@dataclass
class NutrientBound:
    """
    An extra nutrient constraint on top of (or overriding) the default
    NASEM requirement floor. Two uses:
      1. A nutrient with NO default requirement floor of its own (e.g.
         NDF has no NASEM "requirement" equation) -- this is the only
         way to constrain it.
      2. Overriding a nutrient that DOES have a default requirement
         floor (e.g. loosening a mineral's minimum) -- set
         override_default=True to signal this REPLACES the default
         floor rather than adding an extra constraint alongside it.
         solve_diet will raise, not guess, if override_default=False is
         used to set a min BELOW an existing default requirement floor,
         since that combination is ambiguous (add both? which wins?).
    """

    nutrient: str  # e.g. "NDF", "NEL", "MP", or a mineral/vitamin symbol like "Ca"
    min_value: float | None = None
    max_value: float | None = None
    unit: str | None = None  # informational only, not enforced numerically here
    override_default: bool = False

    def __post_init__(self) -> None:
        if self.min_value is None and self.max_value is None:
            raise ValueError(f"{self.nutrient!r}: must specify min_value and/or max_value")
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError(
                f"{self.nutrient!r}: min_value ({self.min_value}) exceeds max_value ({self.max_value})"
            )


@dataclass
class SolveRequest:
    """
    Complete input to solve_diet (not yet built). Bundles the animal,
    the candidate feed universe, and every constraint/objective choice
    on top of the default NASEM requirement floors.
    """

    animal: AnimalState
    milk: MilkTarget
    objective: ObjectiveSpec
    candidate_feeds: list[str]
    ingredient_bounds: list[IngredientBound] = field(default_factory=list)
    nutrient_bounds: list[NutrientBound] = field(default_factory=list)

    # PLACEHOLDER -- see module docstring. Not used by anything yet.
    dmi_mode: Literal["predict", "actual"] = "predict"
    known_dmi_kg: float | None = None

    def __post_init__(self) -> None:
        if not self.candidate_feeds:
            raise ValueError("candidate_feeds cannot be empty")
        if len(self.candidate_feeds) != len(set(self.candidate_feeds)):
            raise ValueError("candidate_feeds contains duplicate names")

        candidate_set = set(self.candidate_feeds)
        for bound in self.ingredient_bounds:
            if bound.feed_name not in candidate_set:
                raise ValueError(
                    f"IngredientBound for {bound.feed_name!r} references a feed not "
                    f"in candidate_feeds"
                )
        bounded_feeds = [b.feed_name for b in self.ingredient_bounds]
        if len(bounded_feeds) != len(set(bounded_feeds)):
            raise ValueError("ingredient_bounds contains more than one bound for the same feed")

        if self.dmi_mode == "actual" and self.known_dmi_kg is None:
            raise ValueError("dmi_mode='actual' requires known_dmi_kg")

    def missing_feed_names(self) -> list[str]:
        """Candidate feed names not found in the real feed library.
        Empty list = all valid. Mirrors Ration.validate_feedstuffs_exist()."""
        import nasem_dairy as nd

        missing = []
        for name in self.candidate_feeds:
            if len(nd.select_feeds([name])) == 0:
                missing.append(name)
        return missing

    def missing_prices(self) -> list[str]:
        """Candidate feeds with no price entry, when the objective needs
        pricing. Empty list if the objective doesn't need prices, or if
        every candidate feed has one."""
        if not self.objective.needs_prices():
            return []
        return [f for f in self.candidate_feeds if f not in self.objective.feed_prices]
