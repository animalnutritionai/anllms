"""
Water requirement (predicted voluntary free water intake) — NASEM (2021),
Equation 9-1 (Chapter 9, "Water").

    An_WaIn (kg/d) = -91.1 + 2.93*Dt_DMIn + 0.61*Dt_DM
                     + 0.062*(Dt_Na/0.023 + Dt_K/0.039)*10
                     + 2.49*Dt_CP + 0.76*Env_TempCurr

Source: Appuhamy et al. (2016). The book states explicitly that this
equation (over the DMI-free alternative, Eq. 9-2) is the recommended
choice "when reliable estimates of dry matter intake (DMI) are
available" -- which this codebase always has, since DMI is a required
input throughout.

SCOPE (per this codebase's request): treated as the water REQUIREMENT
under the assumption of ad libitum access, per project scope -- water
SUPPLY is not modeled (the cow is assumed to always have access to meet
this predicted intake). This mirrors how NASEM itself treats this
number: it's a PREDICTION of voluntary intake (An_WaIn), not a named
"requirement," but functions as the practical requirement figure when
water is freely available, which is the standard management assumption
this equation was fit under.

SCOPE: lactating cows only, consistent with the rest of this codebase.
Heifers and dry cows use a different published equation (not the same
coefficients), and calves have no equation at all in the reference
software (returns None) -- neither is implemented here.

CORRECTION (found while wiring this into RequirementsReport): an earlier
version of this file incorrectly assumed Dt_DM had to be passed as a
0-1 FRACTION (e.g. 0.68), based on a unit test fixture that happened to
use that number. Checking against a REAL full-model run showed the
pipeline actually uses Dt_DM as a PERCENTAGE (e.g. 64.9, not 0.649) --
consistent with every other diet composition field in this codebase
(Dt_NDF, Dt_ADF, etc. are always %). The reference function itself does
no internal unit conversion; it simply uses whatever number is passed.
The fixture's 0.68 was very likely a synthetic test value, not a
realistic diet's actual DM fraction. Fixed here; the isolated fixture
test remains valid as a pass-through arithmetic check, but a second test
against realistic percentage-scale values was added to catch this
category of error in the future.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class WaterRequirementLactatingNASEM2021(KnowledgeEquation):
    """Predicted water requirement for lactating cows, ad lib access assumed (NASEM 2021, Eq. 9-1)."""

    name = "Water requirement (predicted voluntary intake) -- lactating cows"

    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="9", section="Water",
        equation_number="Equation 9-1 (Appuhamy et al., 2016)",
    )

    variables = [
        Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d"),
        Variable(symbol="Dt_DM", name="Diet dry matter content", unit="% (0-100)",
                  description="e.g. 65.0 for a 65% DM diet -- a PERCENTAGE, "
                              "consistent with every other diet composition "
                              "field in this codebase (Dt_NDF, Dt_ADF, etc.), "
                              "confirmed against a real full-model run."),
        Variable(symbol="Dt_Na", name="Dietary sodium concentration", unit="% of DM"),
        Variable(symbol="Dt_K", name="Dietary potassium concentration", unit="% of DM"),
        Variable(symbol="Dt_CP", name="Dietary crude protein concentration", unit="% of DM"),
        Variable(symbol="Env_TempCurr", name="Current ambient temperature", unit="deg C"),
    ]

    formula_text = (
        "An_WaIn (kg/d) = -91.1 + 2.93*DMIn + 0.61*DM_pct "
        "+ 0.62*(Na/0.023 + K/0.039) + 2.49*CP + 0.76*TempCurr"
    )

    assumptions = [
        "Dt_DM is a PERCENTAGE (0-100), matching every other diet "
        "composition field elsewhere in this codebase -- verified "
        "against a real full-model run, not assumed from a unit test "
        "fixture (see module docstring's CORRECTION note).",
        "Sodium and potassium terms are scaled by fixed reference "
        "concentrations (0.023 for Na, 0.039 for K) reflecting their "
        "respective effects on water intake via osmotic/electrolyte "
        "balance, not a simple linear coefficient.",
        "Assumes ad libitum water access -- this equation predicts "
        "voluntary intake under free access, not a minimum survival "
        "requirement. Actual intake under restricted access could be "
        "lower, with production/health consequences not captured here.",
    ]

    applicability = (
        "Lactating dairy cows with known DMI, diet composition, and "
        "ambient temperature. The book explicitly recommends this "
        "DMI-based equation over the DMI-free alternative (Eq. 9-2) "
        "whenever DMI is known."
    )

    limitations = [
        "Regression-based prediction; the book notes some low-DMI/CP/Na "
        "scenarios can produce implausibly low predicted intake (below "
        "the ~22 kg/d minimum seen in the underlying observed data) -- "
        "flagged directly in the reference software's own source comments.",
        "Does not account for water quality, availability, or individual "
        "cow variation beyond the modeled factors.",
    ]

    software_reference = NASEM_DAIRY_2021_SOFTWARE

    known_discrepancies = [
        "Heifers and dry cows use a DIFFERENT published equation (not "
        "simply the same formula with different coefficients) -- not "
        "implemented in this codebase, which is scoped to lactating cows "
        "throughout. Calves have no water intake equation at all in the "
        "reference software.",
    ]

    def calculate(
        self,
        dmi_kg: float,
        diet_dm_pct: float,
        diet_na_pct: float,
        diet_k_pct: float,
        diet_cp_pct: float,
        ambient_temp_c: float,
    ) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        if not (0 < diet_dm_pct <= 100):
            raise ValueError(
                f"diet_dm_pct={diet_dm_pct} is outside a plausible 0-100% "
                f"range. This equation expects a PERCENTAGE (e.g. 65.0 for "
                f"a 65% DM diet), not a fraction (0.65)."
            )

        import nasem_dairy as nd

        value = nd.calculate_An_WaIn(
            An_StatePhys="Lactating Cow",
            Dt_DMIn=dmi_kg,
            Dt_DM=diet_dm_pct,
            Dt_Na=diet_na_pct,
            Dt_K=diet_k_pct,
            Dt_CP=diet_cp_pct,
            Env_TempCurr=ambient_temp_c,
        )

        return EquationResult(
            value=value,
            unit="kg/d (approx. equivalent to L/d)",
            inputs_used={
                "DMI (kg/d)": dmi_kg,
                "Diet DM (%)": diet_dm_pct,
                "Diet Na (%)": diet_na_pct,
                "Diet K (%)": diet_k_pct,
                "Diet CP (%)": diet_cp_pct,
                "Ambient temp (C)": ambient_temp_c,
            },
            equation=self,
        )
