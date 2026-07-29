"""
Zinc (Zn) requirement — NASEM (2021), Equations 20-484 through 20-487.

    An_Zn_m (mg/d) = 5.0 * Dt_DMIn                        [Eq. 20-484]
    An_Zn_g (mg/d) = 24 * Body_Gain                        [Eq. 20-485]
    An_Zn_y (mg/d) = 0 if GestDay<=190, else 0.017*BW       [Eq. 20-486]
    An_Zn_l (mg/d) = 4.0 * MilkProd                         [Eq. 20-487]
    An_Zn_req = An_Zn_m + An_Zn_g + An_Zn_y + An_Zn_l

(Equation 20-483 is the calf-specific formula, not implemented here.)
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class ZincMaintenanceNASEM2021(KnowledgeEquation):
    """Zinc requirement for maintenance (NASEM 2021, Eq. 20-484)."""

    name = "Zinc requirement for maintenance"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-484")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "An_Zn_m (mg/d) = 5.0 * Dt_DMIn"
    assumptions = ["Unlike most other minerals, zinc maintenance is DMI-proportional rather than BW-proportional."]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Zn_m(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)


class ZincGrowthNASEM2021(KnowledgeEquation):
    """Zinc requirement for growth (NASEM 2021, Eq. 20-485)."""

    name = "Zinc requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-485")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Zn_g (mg/d) = 24 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Zn_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class ZincGestationNASEM2021(KnowledgeEquation):
    """Zinc requirement for gestation -- step function (NASEM 2021, Eq. 20-486)."""

    name = "Zinc requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-486")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Zn_y (mg/d) = 0 if GestDay<=190, else 0.017*BW"
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

        value = nd.calculate_An_Zn_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="mg/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class ZincLactationNASEM2021(KnowledgeEquation):
    """Zinc requirement for lactation (NASEM 2021, Eq. 20-487)."""

    name = "Zinc requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-487")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Zn_l (mg/d) = 4.0 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Zn_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="mg/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class ZincRequirementNASEM2021(KnowledgeEquation):
    """Total zinc requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total zinc (Zn) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-484, 20-485, 20-486, 20-487")
    variables = [
        Variable(symbol="An_Zn_m", name="Maintenance Zn", unit="mg/d"),
        Variable(symbol="An_Zn_g", name="Growth Zn", unit="mg/d"),
        Variable(symbol="An_Zn_y", name="Gestation Zn", unit="mg/d"),
        Variable(symbol="An_Zn_l", name="Lactation Zn", unit="mg/d"),
    ]
    formula_text = "An_Zn_req = An_Zn_m + An_Zn_g + An_Zn_y + An_Zn_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, dmi_kg: float, body_gain_kg_per_day: float, gestation_day: int, bw_kg: float, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = ZincMaintenanceNASEM2021().calculate(dmi_kg=dmi_kg)
        growth = ZincGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = ZincGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = ZincLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="mg/d",
            inputs_used={
                "Maintenance (mg/d)": maintenance.value, "Growth (mg/d)": growth.value,
                "Gestation (mg/d)": gestation.value, "Lactation (mg/d)": lactation.value,
            },
            equation=self,
        )
