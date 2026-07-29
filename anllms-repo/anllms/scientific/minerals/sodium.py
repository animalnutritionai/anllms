"""
Sodium (Na) requirement — NASEM (2021), Equations 20-410 through 20-413.

Maintenance is fecal-loss-only (no urinary term, unlike potassium):

    Fe_Na_m (g/d) = 1.45 * Dt_DMIn                        [Eq. 20-410]
    An_Na_g (g/d) = 1.4 * Body_Gain                        [Eq. 20-411]
    An_Na_y (g/d) = 0 if GestDay<=190, else 1.4*(BW/715)    [Eq. 20-412,
                     same step-function pattern as Mg/Cl/K gestation]
    An_Na_l (g/d) = 0.4 * MilkProd                          [Eq. 20-413]
    An_Na_req = Fe_Na_m + An_Na_g + An_Na_y + An_Na_l
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class SodiumMaintenanceNASEM2021(KnowledgeEquation):
    """Sodium requirement for maintenance: fecal only (NASEM 2021, Eq. 20-410)."""

    name = "Sodium requirement for maintenance (fecal loss)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-410")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "Fe_Na_m (g/d) = 1.45 * Dt_DMIn"
    assumptions = ["Unlike potassium, sodium maintenance has NO separate urinary loss term -- fecal loss alone is used, confirmed against the reference software (no Ur_Na_m function exists)."]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_Fe_Na_m(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)


class SodiumGrowthNASEM2021(KnowledgeEquation):
    """Sodium requirement for growth (NASEM 2021, Eq. 20-411)."""

    name = "Sodium requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-411")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Na_g (g/d) = 1.4 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Na_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="g/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class SodiumGestationNASEM2021(KnowledgeEquation):
    """Sodium requirement for gestation -- step function (NASEM 2021, Eq. 20-412)."""

    name = "Sodium requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-412")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Na_y (g/d) = 0 if GestDay<=190, else 1.4*(BW/715)"
    assumptions = ["Step function, same pattern as magnesium/chlorine/potassium gestation: exactly zero until day 190, then a fixed BW-scaled amount."]
    applicability = "Pregnant dairy cattle, particularly relevant in late gestation."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Na_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class SodiumLactationNASEM2021(KnowledgeEquation):
    """Sodium requirement for lactation (NASEM 2021, Eq. 20-413)."""

    name = "Sodium requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-413")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Na_l (g/d) = 0.4 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Na_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class SodiumRequirementNASEM2021(KnowledgeEquation):
    """Total sodium requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total sodium (Na) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-410, 20-411, 20-412, 20-413")
    variables = [
        Variable(symbol="Fe_Na_m", name="Maintenance Na", unit="g/d"),
        Variable(symbol="An_Na_g", name="Growth Na", unit="g/d"),
        Variable(symbol="An_Na_y", name="Gestation Na", unit="g/d"),
        Variable(symbol="An_Na_l", name="Lactation Na", unit="g/d"),
    ]
    formula_text = "An_Na_req = Fe_Na_m + An_Na_g + An_Na_y + An_Na_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, dmi_kg: float, body_gain_kg_per_day: float, gestation_day: int,
        bw_kg: float, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = SodiumMaintenanceNASEM2021().calculate(dmi_kg=dmi_kg)
        growth = SodiumGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = SodiumGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = SodiumLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="g/d",
            inputs_used={
                "Maintenance (g/d)": maintenance.value, "Growth (g/d)": growth.value,
                "Gestation (g/d)": gestation.value, "Lactation (g/d)": lactation.value,
            },
            equation=self,
        )
