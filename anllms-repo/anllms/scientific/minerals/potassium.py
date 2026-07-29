"""
Potassium (K) requirement — NASEM (2021), Equations 20-431 through 20-435.

Unlike sodium/chlorine, potassium maintenance has BOTH a urinary and
fecal term, and the urinary term depends on whether the cow is lactating:

    Ur_K_m (g/d) = 0.2*BW if lactating (MilkProd>0), else 0.07*BW
        [reflects a higher dietary K requirement for lactating cows,
         ~1.00% of diet DM vs a lower AI for dry cows/growing heifers,
         per the book's own stated targets]
    Fe_K_m (g/d) = 2.5 * Dt_DMIn                           [Eq. 20-431]
    An_K_m (g/d) = Ur_K_m + Fe_K_m                          [Eq. 20-432]
    An_K_g (g/d) = 2.5 * Body_Gain                          [Eq. 20-433]
    An_K_y (g/d) = 0 if GestDay<=190, else 1.03*(BW/715)    [Eq. 20-434]
    An_K_l (g/d) = 1.5 * MilkProd                           [Eq. 20-435]
    An_K_req = An_K_m + An_K_g + An_K_y + An_K_l

NOTE: Ur_K_m's own display equation number was not clearly separated in
the source document extraction (only Fe_K_m and the An_K_m sum appear
individually numbered); cited here as part of the Eq. 20-431/20-432 block.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class PotassiumMaintenanceNASEM2021(KnowledgeEquation):
    """Potassium requirement for maintenance: urinary (lactation-dependent) + fecal (NASEM 2021, Eq. 20-431/20-432)."""

    name = "Potassium requirement for maintenance (urinary + fecal)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-431, 20-432 (urinary term not separately numbered, see module docstring)")
    variables = [
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d", description="Used only to select the urinary K coefficient (lactating vs not)."),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d"),
    ]
    formula_text = "Ur_K_m = 0.2*BW if MilkProd>0 else 0.07*BW; Fe_K_m = 2.5*DMIn; An_K_m = Ur_K_m + Fe_K_m"
    assumptions = [
        "Urinary K coefficient is nearly 3x higher for lactating cows "
        "(0.2 vs 0.07 g/kg BW) -- the book states this reflects a target "
        "dietary K concentration of 1.00% DM for lactating cows, "
        "considerably higher than the AI for dry cows/growing heifers.",
        "Uses milk PRODUCTION (>0) as the lactating/non-lactating switch, "
        "not a separate physiological-state flag.",
    ]
    applicability = "Adult (non-calf) dairy cattle, lactating or dry."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float, bw_kg: float, dmi_kg: float) -> EquationResult:
        if bw_kg <= 0 or dmi_kg <= 0:
            raise ValueError("bw_kg and dmi_kg must be positive")
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        ur_k_m = nd.calculate_Ur_K_m(Trg_MilkProd=milk_yield_kg, An_BW=bw_kg)
        fe_k_m = nd.calculate_Fe_K_m(An_DMIn=dmi_kg)
        an_k_m = nd.calculate_An_K_m(Ur_K_m=ur_k_m, Fe_K_m=fe_k_m)
        return EquationResult(
            value=an_k_m, unit="g/d",
            inputs_used={"Urinary K (g/d)": ur_k_m, "Fecal K (g/d)": fe_k_m, "Milk yield (kg/d)": milk_yield_kg},
            equation=self,
        )


class PotassiumGrowthNASEM2021(KnowledgeEquation):
    """Potassium requirement for growth (NASEM 2021, Eq. 20-433)."""

    name = "Potassium requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-433")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_K_g (g/d) = 2.5 * Body_Gain"
    assumptions = []
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_K_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="g/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class PotassiumGestationNASEM2021(KnowledgeEquation):
    """Potassium requirement for gestation -- step function (NASEM 2021, Eq. 20-434)."""

    name = "Potassium requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-434")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_K_y (g/d) = 0 if GestDay<=190, else 1.03*(BW/715)"
    assumptions = ["Step function, same pattern as magnesium/sodium/chlorine gestation."]
    applicability = "Pregnant dairy cattle, particularly relevant in late gestation."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_K_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class PotassiumLactationNASEM2021(KnowledgeEquation):
    """Potassium requirement for lactation (NASEM 2021, Eq. 20-435)."""

    name = "Potassium requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-435")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_K_l (g/d) = 1.5 * MilkProd"
    assumptions = []
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_K_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class PotassiumRequirementNASEM2021(KnowledgeEquation):
    """Total potassium requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total potassium (K) requirement"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Sum of Equations 20-432, 20-433, 20-434, 20-435")
    variables = [
        Variable(symbol="An_K_m", name="Maintenance K", unit="g/d"),
        Variable(symbol="An_K_g", name="Growth K", unit="g/d"),
        Variable(symbol="An_K_y", name="Gestation K", unit="g/d"),
        Variable(symbol="An_K_l", name="Lactation K", unit="g/d"),
    ]
    formula_text = "An_K_req = An_K_m + An_K_g + An_K_y + An_K_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, milk_yield_kg: float, bw_kg: float, dmi_kg: float,
        body_gain_kg_per_day: float, gestation_day: int,
    ) -> EquationResult:
        maintenance = PotassiumMaintenanceNASEM2021().calculate(milk_yield_kg=milk_yield_kg, bw_kg=bw_kg, dmi_kg=dmi_kg)
        growth = PotassiumGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = PotassiumGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = PotassiumLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="g/d",
            inputs_used={
                "Maintenance (g/d)": maintenance.value, "Growth (g/d)": growth.value,
                "Gestation (g/d)": gestation.value, "Lactation (g/d)": lactation.value,
            },
            equation=self,
        )
