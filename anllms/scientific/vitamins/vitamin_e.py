"""
Vitamin E requirement — NASEM (2021), Equation 20-495.

Most complex of the three vitamins -- has THREE layered rules, not one
simple formula:

    Base: An_VitE_req (IU/d) = 2*BW    if dry (MilkProd=0 and Parity>=1) or a calf
                              = 0.8*BW  if lactating
    Override: = 3*BW  if within 21 days of calving (GestDay>=259, assuming
               a 280-day gestation) AND actually pregnant -- this OVERRIDES
               the base value above, does not add to it.
    Pasture credit: requirement is REDUCED by 50 IU per kg of pasture DM
               intake (grazing cattle need less supplemental vitamin E),
               capped so the requirement cannot go below zero.

The book's own text (Chapter 20) states this pasture credit explicitly:
"If animals are grazing, the vitamin E requirement is reduced by 50 IU/kg
of pasture DM intake. The contribution is capped at the total vitamin E
requirement" -- confirmed directly from the primary text, not just the
software.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class VitaminERequirementNASEM2021(KnowledgeEquation):
    """Total vitamin E requirement (NASEM 2021, Eq. 20-495)."""

    name = "Total vitamin E requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="7/20",
        equation_number="Equation 20-495 (confident attribution by position; "
                         "formula text itself had a source-extraction gap)",
    )
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d"),
        Variable(symbol="An_Parity_rl", name="Parity", unit="count"),
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_Preg", name="Pregnant flag", unit="0/1"),
        Variable(symbol="Dt_PastIn", name="Pasture DM intake", unit="kg/d"),
    ]
    formula_text = (
        "Base: 2*BW (dry cow or calf) or 0.8*BW (lactating); "
        "Override: 3*BW if within 21 days of calving AND pregnant; "
        "Final: base/override MINUS 50*Dt_PastIn, floored at 0"
    )
    assumptions = [
        "The close-up dry cow override (3*BW, triggered at GestDay>=259) "
        "REPLACES the base value entirely rather than adding to it -- "
        "confirmed against real fixture data (a pregnant cow at GestDay=287 "
        "gets exactly 2052 IU = 3*704, not 2*704+3*704).",
        "The override applies regardless of lactating/dry status as long "
        "as An_Preg=1 and GestDay>=259 -- confirmed via fixture showing "
        "identical output (2052) for both 'Lactating Cow' and 'Dry Cow' "
        "state at the same late gestation day.",
        "Pasture credit (50 IU/kg pasture DMI) is subtracted AFTER the "
        "base/override selection, and the whole requirement is floored "
        "at zero -- a cow cannot end up with a negative vitamin E "
        "requirement even on very high pasture intake.",
    ]
    applicability = "All non-calf dairy cattle."
    limitations = [
        "The 259-day gestation-day threshold assumes a ~280-day gestation "
        "length; does not automatically adjust for breeds/individuals "
        "with meaningfully different typical gestation lengths.",
    ]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, bw_kg: float, milk_yield_kg: float, parity: int,
        gestation_day: int, is_pregnant: bool, pasture_dmi_kg: float = 0.0,
    ) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        if pasture_dmi_kg < 0:
            raise ValueError("pasture_dmi_kg cannot be negative")

        import nasem_dairy as nd

        value = nd.calculate_An_VitE_req(
            Trg_MilkProd=milk_yield_kg,
            An_Parity_rl=parity,
            An_StatePhys="Lactating Cow" if milk_yield_kg > 0 else "Dry Cow",
            An_BW=bw_kg,
            An_GestDay=gestation_day,
            An_Preg=1 if is_pregnant else 0,
            Dt_PastIn=pasture_dmi_kg,
        )
        return EquationResult(
            value=value, unit="IU/d",
            inputs_used={
                "BW (kg)": bw_kg, "Milk yield (kg/d)": milk_yield_kg,
                "Parity": parity, "Gestation day": gestation_day,
                "Pregnant": is_pregnant, "Pasture DMI (kg/d)": pasture_dmi_kg,
            },
            equation=self,
        )


class VitaminESupplyNASEM2021(KnowledgeEquation):
    """Vitamin E supply from the diet (NASEM 2021, part of Eq. 20-496)."""

    name = "Vitamin E supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="7/20", equation_number="Dt_VitEIn, used directly in balance Equation 20-496")
    variables = [Variable(symbol="Dt_VitEIn", name="Dietary vitamin E intake", unit="IU/d")]
    formula_text = "Supply = Dt_VitEIn = sum(Fd_VitEIn) across ration -- no absorption coefficient applied"
    assumptions = ["No modeled absorption efficiency for vitamin E -- raw summed dietary intake used directly as supply."]
    applicability = "Any lactating dairy cow diet."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Dt_VitEIn")
        return EquationResult(value=value, unit="IU/d", inputs_used={"Source": "Dt_VitEIn from shared model run"}, equation=self)
