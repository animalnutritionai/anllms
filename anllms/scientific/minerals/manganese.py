"""
Manganese (Mn) requirement — NASEM (2021), Equations 20-470, 20-472, 20-473, 20-474.

    An_Mn_m (mg/d) = 0.0026 * BW                          [Eq. 20-470]
    An_Mn_g (mg/d) = 0.7 * Body_Gain                       [Eq. 20-472]
    An_Mn_y (mg/d) = 0 if GestDay<=190, else 0.00042*BW    [Eq. 20-473]
    An_Mn_l (mg/d) = 0.03 * MilkProd                       [Eq. 20-474]
    An_Mn_req = An_Mn_m + An_Mn_g + An_Mn_y + An_Mn_l

(Equation 20-471 is the calf-specific formula, not implemented here.)
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class ManganeseMaintenanceNASEM2021(KnowledgeEquation):
    """Manganese requirement for maintenance (NASEM 2021, Eq. 20-470)."""

    name = "Manganese requirement for maintenance"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-470")
    variables = [Variable(symbol="An_BW", name="Body weight", unit="kg")]
    formula_text = "An_Mn_m (mg/d) = 0.0026 * BW"
    assumptions = []
    applicability = "Adult (non-calf) dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Mn_m(An_BW=bw_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"BW (kg)": bw_kg}, equation=self)


class ManganeseGrowthNASEM2021(KnowledgeEquation):
    """Manganese requirement for growth (NASEM 2021, Eq. 20-472)."""

    name = "Manganese requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-472")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Mn_g (mg/d) = 0.7 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Mn_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class ManganeseGestationNASEM2021(KnowledgeEquation):
    """Manganese requirement for gestation -- step function (NASEM 2021, Eq. 20-473)."""

    name = "Manganese requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-473")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Mn_y (mg/d) = 0 if GestDay<=190, else 0.00042*BW"
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

        value = nd.calculate_An_Mn_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="mg/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class ManganeseLactationNASEM2021(KnowledgeEquation):
    """Manganese requirement for lactation (NASEM 2021, Eq. 20-474)."""

    name = "Manganese requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-474")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Mn_l (mg/d) = 0.03 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Mn_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class ManganeseRequirementNASEM2021(KnowledgeEquation):
    """Total manganese requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total manganese (Mn) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-470, 20-472, 20-473, 20-474")
    variables = [
        Variable(symbol="An_Mn_m", name="Maintenance Mn", unit="mg/d"),
        Variable(symbol="An_Mn_g", name="Growth Mn", unit="mg/d"),
        Variable(symbol="An_Mn_y", name="Gestation Mn", unit="mg/d"),
        Variable(symbol="An_Mn_l", name="Lactation Mn", unit="mg/d"),
    ]
    formula_text = "An_Mn_req = An_Mn_m + An_Mn_g + An_Mn_y + An_Mn_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, bw_kg: float, body_gain_kg_per_day: float, gestation_day: int, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = ManganeseMaintenanceNASEM2021().calculate(bw_kg=bw_kg)
        growth = ManganeseGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = ManganeseGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = ManganeseLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="mg/d",
            inputs_used={
                "Maintenance (mg/d)": maintenance.value, "Growth (mg/d)": growth.value,
                "Gestation (mg/d)": gestation.value, "Lactation (mg/d)": lactation.value,
            },
            equation=self,
        )


class ManganeseSupplyNASEM2021(KnowledgeEquation):
    """Absorbed manganese supply from the diet (NASEM 2021, Eq. 20-468/20-469)."""

    name = "Absorbed manganese (Mn) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-468, 20-469")
    variables = [
        Variable(symbol="Fd_MnInf", name="Manganese intake per ingredient", unit="mg/d"),
        Variable(symbol="Fd_acMnf", name="Absorption coefficient per ingredient", unit="mg/mg"),
    ]
    formula_text = "Fd_absMnInf = Fd_MnInf * Fd_acMnf; Abs_MnIn = sum(Fd_absMnInf) across ration"
    assumptions = ["Per-ingredient absorption coefficient from the real feed library."]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_MnIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this codebase.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_MnIn")
        return EquationResult(value=value, unit="mg/d", inputs_used={"Source": "Abs_MnIn from shared model run"}, equation=self)
