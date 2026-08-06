"""
Chlorine (Cl) requirement — NASEM (2021), Equations 20-420 through 20-423.

Same shape as sodium (fecal-only maintenance, step-function gestation):

    Fe_Cl_m (g/d) = 1.11 * Dt_DMIn                        [Eq. 20-420]
    An_Cl_g (g/d) = 1.0 * Body_Gain                        [Eq. 20-421]
    An_Cl_y (g/d) = 0 if GestDay<=190, else 1.0*(BW/715)    [Eq. 20-422]
    An_Cl_l (g/d) = 1.0 * MilkProd                          [Eq. 20-423]
    An_Cl_req = Fe_Cl_m + An_Cl_g + An_Cl_y + An_Cl_l
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class ChlorineMaintenanceNASEM2021(KnowledgeEquation):
    """Chlorine requirement for maintenance: fecal only (NASEM 2021, Eq. 20-420)."""

    name = "Chlorine requirement for maintenance (fecal loss)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-420")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "Fe_Cl_m (g/d) = 1.11 * Dt_DMIn"
    assumptions = ["No separate urinary loss term, same pattern as sodium."]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_Fe_Cl_m(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)


class ChlorineGrowthNASEM2021(KnowledgeEquation):
    """Chlorine requirement for growth (NASEM 2021, Eq. 20-421)."""

    name = "Chlorine requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-421")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Cl_g (g/d) = 1.0 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Cl_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="g/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class ChlorineGestationNASEM2021(KnowledgeEquation):
    """Chlorine requirement for gestation -- step function (NASEM 2021, Eq. 20-422)."""

    name = "Chlorine requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-422")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Cl_y (g/d) = 0 if GestDay<=190, else 1.0*(BW/715)"
    assumptions = ["Step function, same pattern as magnesium/sodium/potassium gestation."]
    applicability = "Pregnant dairy cattle, particularly relevant in late gestation."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Cl_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class ChlorineLactationNASEM2021(KnowledgeEquation):
    """Chlorine requirement for lactation (NASEM 2021, Eq. 20-423)."""

    name = "Chlorine requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-423")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Cl_l (g/d) = 1.0 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Cl_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class ChlorineRequirementNASEM2021(KnowledgeEquation):
    """Total chlorine requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total chlorine (Cl) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-420, 20-421, 20-422, 20-423")
    variables = [
        Variable(symbol="Fe_Cl_m", name="Maintenance Cl", unit="g/d"),
        Variable(symbol="An_Cl_g", name="Growth Cl", unit="g/d"),
        Variable(symbol="An_Cl_y", name="Gestation Cl", unit="g/d"),
        Variable(symbol="An_Cl_l", name="Lactation Cl", unit="g/d"),
    ]
    formula_text = "An_Cl_req = Fe_Cl_m + An_Cl_g + An_Cl_y + An_Cl_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, dmi_kg: float, body_gain_kg_per_day: float, gestation_day: int,
        bw_kg: float, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = ChlorineMaintenanceNASEM2021().calculate(dmi_kg=dmi_kg)
        growth = ChlorineGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = ChlorineGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = ChlorineLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="g/d",
            inputs_used={
                "Maintenance (g/d)": maintenance.value, "Growth (g/d)": growth.value,
                "Gestation (g/d)": gestation.value, "Lactation (g/d)": lactation.value,
            },
            equation=self,
        )


class ChlorineSupplyNASEM2021(KnowledgeEquation):
    """Absorbed chlorine supply from the diet (NASEM 2021, Eq. 20-417/20-418)."""

    name = "Absorbed chlorine (Cl) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-417, 20-418")
    variables = [
        Variable(symbol="Fd_ClInf", name="Chlorine intake per ingredient", unit="g/d"),
        Variable(symbol="Fd_acClf", name="Absorption coefficient per ingredient", unit="g/g"),
    ]
    formula_text = "Fd_absClInf = Fd_ClInf * Fd_acClf; Abs_ClIn = sum(Fd_absClInf) across ration"
    assumptions = ["Per-ingredient absorption coefficient from the real feed library."]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_ClIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this codebase.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_ClIn")
        return EquationResult(value=value, unit="g/d", inputs_used={"Source": "Abs_ClIn from shared model run"}, equation=self)
