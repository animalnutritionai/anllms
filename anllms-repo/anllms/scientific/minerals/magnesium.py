"""
Magnesium (Mg) requirement — NASEM (2021), Equations 20-398 through 20-404.

Simpler than calcium/phosphorus: no allometric BW-scaling terms, and
gestation Mg is a STEP FUNCTION (zero until day 190, then a fixed
BW-scaled amount) rather than a continuous exponential curve.

    Ur_Mg_m (g/d) = 0.0007 * BW                          [Eq. 20-398]
    Fe_Mg_m (g/d) = 0.3 * Dt_DMIn                         [Eq. 20-399]
    An_Mg_m (g/d) = Ur_Mg_m + Fe_Mg_m                     [Eq. 20-400/20-401]
    An_Mg_g (g/d) = 0.45 * Body_Gain                      [Eq. 20-402, see note]
    An_Mg_y (g/d) = 0 if GestDay<=190, else 0.3*(BW/715)  [equation number
                     unclear -- see NOTE below]
    An_Mg_l (g/d) = 0.11 * MilkProd                       [Eq. 20-403]
    An_Mg_req = An_Mg_m + An_Mg_g + An_Mg_y + An_Mg_l

NOTE on equation numbering: the source document has a text-extraction gap
in this section -- two consecutive "(Equation 20-402)" labels appear with
no formula text between them, suggesting the growth and gestation formulas
were both compressed into that gap during extraction (likely from a table
or image in the original PDF/book that didn't extract as text). Growth is
confidently Eq. 20-402 based on position; gestation's exact number is NOT
confirmed and should be verified against a paginated copy of the book
before being cited elsewhere as authoritative. Flagged honestly rather
than guessed.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class MagnesiumMaintenanceNASEM2021(KnowledgeEquation):
    """Magnesium requirement for maintenance: urinary + fecal (NASEM 2021, Eq. 20-398 to 20-401)."""

    name = "Magnesium requirement for maintenance (urinary + fecal)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-398, 20-399, 20-400/20-401")
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d"),
    ]
    formula_text = "Ur_Mg_m = 0.0007 * BW; Fe_Mg_m = 0.3 * DMIn; An_Mg_m = Ur_Mg_m + Fe_Mg_m"
    assumptions = ["Fecal loss coefficient (0.3 g/kg DMI) is constant, not parity-dependent, unlike phosphorus."]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = ["Does not vary by diet Mg concentration or absorption efficiency (handled separately as a distinct absorption coefficient elsewhere in the full model)."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float, dmi_kg: float) -> EquationResult:
        if bw_kg <= 0 or dmi_kg <= 0:
            raise ValueError("bw_kg and dmi_kg must be positive")
        import nasem_dairy as nd

        ur_mg_m = nd.calculate_Ur_Mg_m(An_BW=bw_kg)
        fe_mg_m = nd.calculate_Fe_Mg_m(An_DMIn=dmi_kg)
        an_mg_m = nd.calculate_An_Mg_m(Ur_Mg_m=ur_mg_m, Fe_Mg_m=fe_mg_m)
        return EquationResult(
            value=an_mg_m, unit="g/d",
            inputs_used={"Urinary Mg (g/d)": ur_mg_m, "Fecal Mg (g/d)": fe_mg_m},
            equation=self,
        )


class MagnesiumGrowthNASEM2021(KnowledgeEquation):
    """Magnesium requirement for growth (NASEM 2021, Eq. 20-402)."""

    name = "Magnesium requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-402")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Mg_g (g/d) = 0.45 * Body_Gain"
    assumptions = ["Simple linear relationship, no BW-scaling term (unlike Ca/P growth equations)."]
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Mg_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="g/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class MagnesiumGestationNASEM2021(KnowledgeEquation):
    """Magnesium requirement for gestation -- a step function (NASEM 2021, equation number unconfirmed, see module docstring)."""

    name = "Magnesium requirement for gestation"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Number not confirmed due to a source-document extraction gap -- see module docstring",
    )
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Mg_y (g/d) = 0 if GestDay<=190, else 0.3*(BW/715)"
    assumptions = [
        "UNLIKE calcium/phosphorus gestation (continuous exponential "
        "curves), magnesium gestation requirement is a STEP FUNCTION: "
        "exactly zero for the first 190 days, then a fixed amount for "
        "the remainder of gestation. Confirmed against real fixture data "
        "(GestDay=130 -> 0 exactly; GestDay=200 -> nonzero), not assumed.",
    ]
    applicability = "Pregnant dairy cattle, particularly relevant only in late gestation (>190 days)."
    limitations = ["Equation number not independently confirmed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "The exact book equation number for this formula could not be "
        "confirmed due to a text-extraction gap in the source document "
        "(two consecutive equation-number labels with no formula text "
        "between them). The FORMULA and its step-function behavior are "
        "confirmed against the reference software and real fixture test "
        "data; only the citation number is uncertain. Should be verified "
        "against a paginated copy of the book before being treated as final.",
    ]

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Mg_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class MagnesiumLactationNASEM2021(KnowledgeEquation):
    """Magnesium requirement for lactation (NASEM 2021, Eq. 20-403)."""

    name = "Magnesium requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-403")
    variables = [Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d")]
    formula_text = "An_Mg_l (g/d) = 0.11 * MilkProd"
    assumptions = ["Simple linear relationship; does not vary with milk composition, unlike calcium/phosphorus lactation equations."]
    applicability = "Lactating dairy cattle."
    limitations = []
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Mg_l(Trg_MilkProd=milk_yield_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"Milk yield (kg/d)": milk_yield_kg}, equation=self)


class MagnesiumRequirementNASEM2021(KnowledgeEquation):
    """Total magnesium requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total magnesium (Mg) requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Sum of Equations 20-400/20-401, 20-402, [gestation eq. unconfirmed], 20-403",
    )
    variables = [
        Variable(symbol="An_Mg_m", name="Maintenance Mg", unit="g/d"),
        Variable(symbol="An_Mg_g", name="Growth Mg", unit="g/d"),
        Variable(symbol="An_Mg_y", name="Gestation Mg", unit="g/d"),
        Variable(symbol="An_Mg_l", name="Lactation Mg", unit="g/d"),
    ]
    formula_text = "An_Mg_req = An_Mg_m + An_Mg_g + An_Mg_y + An_Mg_l"
    assumptions = ["Applies to adult (non-calf) cattle."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components, including the unconfirmed gestation equation number."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, bw_kg: float, dmi_kg: float, body_gain_kg_per_day: float,
        gestation_day: int, milk_yield_kg: float,
    ) -> EquationResult:
        maintenance = MagnesiumMaintenanceNASEM2021().calculate(bw_kg=bw_kg, dmi_kg=dmi_kg)
        growth = MagnesiumGrowthNASEM2021().calculate(body_gain_kg_per_day=body_gain_kg_per_day)
        gestation = MagnesiumGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = MagnesiumLactationNASEM2021().calculate(milk_yield_kg=milk_yield_kg)
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="g/d",
            inputs_used={
                "Maintenance (g/d)": maintenance.value, "Growth (g/d)": growth.value,
                "Gestation (g/d)": gestation.value, "Lactation (g/d)": lactation.value,
            },
            equation=self,
        )
