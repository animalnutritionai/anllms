"""
Iron (Fe) requirement — NASEM (2021), Equations 20-461 through 20-463.

UNLIKE every other mineral in this codebase, iron has NO maintenance
term at all -- confirmed directly in the reference software's own source
comment ("no Fe maintenance requirement"), not an oversight on our part.

    An_Fe_g (mg/d) = 34 * Body_Gain                        [Eq. 20-461]
    An_Fe_y (mg/d) = 0 if GestDay<=190, else 0.025*BW        [Eq. 20-462]
    An_Fe_l (mg/d) = 1.0 * MilkProd                          [Eq. 20-463]
    An_Fe_req = An_Fe_g + An_Fe_y + An_Fe_l   (no maintenance term)
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class IronGrowthNASEM2021(KnowledgeEquation):
    """Iron requirement for growth (NASEM 2021, Eq. 20-461)."""

    name = "Iron requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-461")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Fe_g (mg/d) = 34 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Fe_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class IronGestationNASEM2021(KnowledgeEquation):
    """Iron requirement for gestation -- step function (NASEM 2021, Eq. 20-462)."""

    name = "Iron requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-462")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Fe_y (mg/d) = 0 if GestDay<=190, else 0.025*BW"
    assumptions = ["Two-tier step function, same pattern as the macrominerals' gestation equations."]
    applicability = "Pregnant dairy cattle, particularly relevant in late gestation."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Fe_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="mg/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class IronLactationNASEM2021(KnowledgeEquation):
    """Iron requirement for lactation (NASEM 2021, Eq. 20-463)."""

    name = "Iron requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-463")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Fe_l (mg/d) = 1.0 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Fe_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class IronRequirementNASEM2021(KnowledgeEquation):
    """Total iron requirement (NASEM 2021): growth + gestation + lactation -- NO maintenance term."""

    name = "Total iron (Fe) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-461, 20-462, 20-463 (no maintenance equation exists)")
    variables = [
        Variable(symbol="An_Fe_g", name="Growth Fe", unit="mg/d"),
        Variable(symbol="An_Fe_y", name="Gestation Fe", unit="mg/d"),
        Variable(symbol="An_Fe_l", name="Lactation Fe", unit="mg/d"),
    ]
    formula_text = "An_Fe_req = An_Fe_g + An_Fe_y + An_Fe_l   (NO maintenance term)"
    assumptions = [
        "This total has NO maintenance component -- confirmed directly "
        "from the reference software's own source comment stating there "
        "is no Fe maintenance requirement, not an omission in this "
        "wrapper. A dry, non-pregnant, non-growing cow's iron "
        "'requirement' by this equation is therefore exactly zero.",
    ]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant, and/or growing."
    limitations = ["Inherits all limitations of its three components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float, gestation_day: int, bw_kg: float, milk_yield_kg: float) -> EquationResult:
        growth = IronGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = IronGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = IronLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="mg/d",
            inputs_used={"Growth (mg/d)": growth.value, "Gestation (mg/d)": gestation.value, "Lactation (mg/d)": lactation.value},
            equation=self,
        )


class IronSupplyNASEM2021(KnowledgeEquation):
    """Absorbed iron supply from the diet (NASEM 2021, Eq. 20-458/20-459)."""

    name = "Absorbed iron (Fe) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-458, 20-459")
    variables = [
        Variable(symbol="Fd_FeInf", name="Iron intake per ingredient", unit="mg/d"),
        Variable(symbol="Fd_acFef", name="Absorption coefficient per ingredient", unit="mg/mg"),
    ]
    formula_text = "Fd_absFeInf = Fd_FeInf * Fd_acFef; Abs_FeIn = sum(Fd_absFeInf) across ration"
    assumptions = ["Per-ingredient absorption coefficient from the real feed library."]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_FeIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this codebase.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_FeIn")
        return EquationResult(value=value, unit="mg/d", inputs_used={"Source": "Abs_FeIn from shared model run"}, equation=self)
