"""
Copper (Cu) requirement — NASEM (2021), Equations 20-448 through 20-451.

Gestation is a THREE-tier step function (not the simple two-tier 0/nonzero
pattern seen in the macrominerals): zero before day 90, a low rate from
day 90-190, then a higher rate after day 190 -- reflecting accelerating
fetal Cu accretion through gestation.

    An_Cu_m (mg/d) = 0.0145 * BW                           [Eq. 20-448]
    An_Cu_g (mg/d) = 2.0 * Body_Gain                        [Eq. 20-449]
    An_Cu_y (mg/d) = 0 if GestDay<90;
                     0.0003*BW if 90<=GestDay<=190;
                     0.0023*BW if GestDay>190                [Eq. 20-450]
    An_Cu_l (mg/d) = 0.04 * MilkProd                         [Eq. 20-451]
    An_Cu_req = An_Cu_m + An_Cu_g + An_Cu_y + An_Cu_l
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class CopperMaintenanceNASEM2021(KnowledgeEquation):
    """Copper requirement for maintenance (NASEM 2021, Eq. 20-448)."""

    name = "Copper requirement for maintenance"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-448")
    variables = [Variable(symbol="An_BW", name="Body weight", unit="kg")]
    formula_text = "An_Cu_m (mg/d) = 0.0145 * BW"
    assumptions = []
    applicability = "Adult (non-calf) dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Cu_m(An_BW=bw_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"BW (kg)": bw_kg}, equation=self)


class CopperGrowthNASEM2021(KnowledgeEquation):
    """Copper requirement for growth (NASEM 2021, Eq. 20-449)."""

    name = "Copper requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-449")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Cu_g (mg/d) = 2.0 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Cu_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class CopperGestationNASEM2021(KnowledgeEquation):
    """Copper requirement for gestation -- three-tier step function (NASEM 2021, Eq. 20-450)."""

    name = "Copper requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-450")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Cu_y (mg/d) = 0 if GestDay<90; 0.0003*BW if 90<=GestDay<=190; 0.0023*BW if GestDay>190"
    assumptions = [
        "THREE-tier step function, unlike the macrominerals' simpler "
        "two-tier (0/nonzero at day 190) gestation pattern -- confirmed "
        "against real fixture data at three distinct gestation days "
        "(80, 150, 200), each giving a different requirement level.",
    ]
    applicability = "Pregnant dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Cu_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="mg/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class CopperLactationNASEM2021(KnowledgeEquation):
    """Copper requirement for lactation (NASEM 2021, Eq. 20-451)."""

    name = "Copper requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-451")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Cu_l (mg/d) = 0.04 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Cu_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class CopperRequirementNASEM2021(KnowledgeEquation):
    """Total copper requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total copper (Cu) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-448, 20-449, 20-450, 20-451")
    variables = [
        Variable(symbol="An_Cu_m", name="Maintenance Cu", unit="mg/d"),
        Variable(symbol="An_Cu_g", name="Growth Cu", unit="mg/d"),
        Variable(symbol="An_Cu_y", name="Gestation Cu", unit="mg/d"),
        Variable(symbol="An_Cu_l", name="Lactation Cu", unit="mg/d"),
    ]
    formula_text = "An_Cu_req = An_Cu_m + An_Cu_g + An_Cu_y + An_Cu_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, bw_kg: float, body_gain_kg_per_day: float, gestation_day: int, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = CopperMaintenanceNASEM2021().calculate(bw_kg=bw_kg)
        growth = CopperGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = CopperGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = CopperLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="mg/d",
            inputs_used={
                "Maintenance (mg/d)": maintenance.value, "Growth (mg/d)": growth.value,
                "Gestation (mg/d)": gestation.value, "Lactation (mg/d)": lactation.value,
            },
            equation=self,
        )
