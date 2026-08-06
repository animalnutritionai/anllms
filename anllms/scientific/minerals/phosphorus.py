"""
Phosphorus (P) requirement — NASEM (2021), Equations 20-384 through 20-389.

Same factorial pattern as calcium, but maintenance itself has TWO parts
(urinary + fecal, unlike calcium's single fecal-only maintenance term):

    Ur_P_m (g/d) = 0.0006 * BW                                  [Eq. 20-384]
    Fe_P_m (g/d) = 0.8 * Dt_DMIn (heifers) or 1.0 * Dt_DMIn (cows) [Eq. 20-385]
    An_P_m (g/d) = Ur_P_m + Fe_P_m                               [Eq. 20-386]
    An_P_g (g/d) = (1.2 + 4.635*BWmature^0.22*BW^-0.22)*BWgain   [Eq. 20-387]
    An_P_y (g/d) = exponential function of gestation day, BW     [Eq. 20-388]
    An_P_l (g/d) = (0.48 + 0.13*MlkNP_Milk*100) * MilkProd       [Eq. 20-389]
        where MlkNP_Milk = milk true protein as a FRACTION of milk
        weight (i.e. milk_true_protein_pct / 100), NOT the raw percent.
    An_P_req = An_P_m + An_P_g + An_P_y + An_P_l
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class PhosphorusMaintenanceNASEM2021(KnowledgeEquation):
    """Phosphorus requirement for maintenance: urinary + fecal (NASEM 2021, Eq. 20-384 to 20-386)."""

    name = "Phosphorus requirement for maintenance (urinary + fecal)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-384, 20-385, 20-386")
    variables = [
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
        Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d"),
        Variable(symbol="An_Parity_rl", name="Parity", unit="count", description="0 = never calved (heifer); >=1 = cow"),
    ]
    formula_text = (
        "Ur_P_m = 0.0006 * BW\n"
        "Fe_P_m = 0.8 * DMIn (heifer, parity=0) or 1.0 * DMIn (cow, parity>=1)\n"
        "An_P_m = Ur_P_m + Fe_P_m"
    )
    assumptions = [
        "Fecal P loss coefficient differs by parity: 0.8 g/kg DMI for "
        "heifers that have never calved, 1.0 g/kg DMI for cows -- a real "
        "physiological difference, not an approximation collapsed to one "
        "number.",
    ]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = ["Does not vary fecal loss by diet P concentration, only by parity and DMI."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_kg: float, dmi_kg: float, parity: int) -> EquationResult:
        if bw_kg <= 0 or dmi_kg <= 0:
            raise ValueError("bw_kg and dmi_kg must be positive")
        import nasem_dairy as nd

        ur_p_m = nd.calculate_Ur_P_m(An_BW=bw_kg)
        fe_p_m = nd.calculate_Fe_P_m(An_Parity_rl=parity, An_DMIn=dmi_kg)
        an_p_m = nd.calculate_An_P_m(Ur_P_m=ur_p_m, Fe_P_m=fe_p_m)
        return EquationResult(
            value=an_p_m, unit="g/d",
            inputs_used={"Urinary P (g/d)": ur_p_m, "Fecal P (g/d)": fe_p_m, "Parity": parity},
            equation=self,
        )


class PhosphorusGrowthNASEM2021(KnowledgeEquation):
    """Phosphorus requirement for growth (NASEM 2021, Eq. 20-387)."""

    name = "Phosphorus requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-387")
    variables = [
        Variable(symbol="An_BW_mature", name="Mature body weight", unit="kg"),
        Variable(symbol="An_BW", name="Current body weight", unit="kg"),
        Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d"),
    ]
    formula_text = "An_P_g (g/d) = (1.2 + 4.635 * BW_mature^0.22 * BW^-0.22) * Body_Gain"
    assumptions = ["Zero when Body_Gain is zero (this codebase's default for a mature cow)."]
    applicability = "Adult (non-calf) dairy cattle with nonzero targeted body weight gain."
    limitations = ["Empirical allometric relationship."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_mature_kg: float, bw_kg: float, body_gain_kg_per_day: float) -> EquationResult:
        if bw_kg <= 0 or bw_mature_kg <= 0:
            raise ValueError("bw_kg and bw_mature_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_P_g(An_BW_mature=bw_mature_kg, An_BW=bw_kg, Body_Gain=body_gain_kg_per_day)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"BW mature (kg)": bw_mature_kg, "BW (kg)": bw_kg, "Body gain (kg/d)": body_gain_kg_per_day},
            equation=self,
        )


class PhosphorusGestationNASEM2021(KnowledgeEquation):
    """Phosphorus requirement for gestation (NASEM 2021, Eq. 20-388)."""

    name = "Phosphorus requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-388")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_P_y (g/d) = exponential function of gestation day, scaled by BW/715"
    assumptions = ["Same functional form as calcium's gestation equation, with P-specific coefficients."]
    applicability = "Pregnant dairy cattle."
    limitations = ["Not exactly zero at gestation_day=0 -- a rate-curve property, not a bug (same as calcium's gestation equation)."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_P_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class PhosphorusLactationNASEM2021(KnowledgeEquation):
    """Phosphorus requirement for lactation (NASEM 2021, Eq. 20-389)."""

    name = "Phosphorus requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-389")
    variables = [
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d"),
        Variable(symbol="MlkNP_Milk", name="Milk true protein as a fraction of milk weight", unit="fraction"),
    ]
    formula_text = "An_P_l (g/d) = (0.48 + 0.13 * MlkNP_Milk * 100) * MilkProd"
    assumptions = [
        "MlkNP_Milk is milk true protein as a FRACTION (e.g. 0.032 for "
        "3.2%), not the raw percentage -- confirmed by tracing the "
        "reference software's own MlkNP_Milk derivation "
        "(Mlk_NP_g/1000/MilkProd), which reduces to milk_true_protein_pct/100.",
    ]
    applicability = "Lactating dairy cattle."
    limitations = ["Regression fit; individual cows can deviate."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float, milk_true_protein_pct: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd

        mlk_np_milk_fraction = milk_true_protein_pct / 100
        value = nd.calculate_An_P_l(Trg_MilkProd=milk_yield_kg, MlkNP_Milk=mlk_np_milk_fraction)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={
                "Milk yield (kg/d)": milk_yield_kg,
                "Milk true protein (%)": milk_true_protein_pct,
                "MlkNP_Milk (fraction)": mlk_np_milk_fraction,
            },
            equation=self,
        )


class PhosphorusRequirementNASEM2021(KnowledgeEquation):
    """Total phosphorus requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total phosphorus (P) requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Sum of Equations 20-386, 20-387, 20-388, 20-389",
    )
    variables = [
        Variable(symbol="An_P_m", name="Maintenance P", unit="g/d"),
        Variable(symbol="An_P_g", name="Growth P", unit="g/d"),
        Variable(symbol="An_P_y", name="Gestation P", unit="g/d"),
        Variable(symbol="An_P_l", name="Lactation P", unit="g/d"),
    ]
    formula_text = "An_P_req = An_P_m + An_P_g + An_P_y + An_P_l"
    assumptions = ["Applies to adult (non-calf) cattle; calves use a separate combined equation (Eq. 20-383) not implemented here."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, bw_kg: float, dmi_kg: float, parity: int, bw_mature_kg: float,
        body_gain_kg_per_day: float, gestation_day: int,
        milk_yield_kg: float, milk_true_protein_pct: float,
    ) -> EquationResult:
        maintenance = PhosphorusMaintenanceNASEM2021().calculate(bw_kg=bw_kg, dmi_kg=dmi_kg, parity=parity)
        growth = PhosphorusGrowthNASEM2021().calculate(
            bw_mature_kg=bw_mature_kg, bw_kg=bw_kg, body_gain_kg_per_day=body_gain_kg_per_day
        )
        gestation = PhosphorusGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = PhosphorusLactationNASEM2021().calculate(
            milk_yield_kg=milk_yield_kg, milk_true_protein_pct=milk_true_protein_pct
        )
        total = maintenance.value + growth.value + gestation.value + lactation.value
        return EquationResult(
            value=total, unit="g/d",
            inputs_used={
                "Maintenance (g/d)": maintenance.value, "Growth (g/d)": growth.value,
                "Gestation (g/d)": gestation.value, "Lactation (g/d)": lactation.value,
            },
            equation=self,
        )


class PhosphorusSupplyNASEM2021(KnowledgeEquation):
    """Absorbed phosphorus supply from the diet (NASEM 2021, Eq. 20-381/20-382)."""

    name = "Absorbed phosphorus (P) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-381, 20-382")
    variables = [
        Variable(symbol="Fd_PInf", name="Phosphorus intake per ingredient", unit="g/d"),
        Variable(symbol="Fd_acPtotf", name="Absorption coefficient per ingredient", unit="g/g"),
    ]
    formula_text = "Fd_absPInf = Fd_PInf * Fd_acPtotf; Abs_PIn = sum(Fd_absPInf) across ration"
    assumptions = [
        "Absorption coefficient for non-mineral-supplement ingredients is "
        "itself derived from inorganic vs organic P fractions (0.84 AC "
        "for inorganic P, 0.68 for organic P, per the book), not a single "
        "flat P absorption rate.",
    ]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_PIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this "
        "codebase. Formula/citation confirmed correct; computation not "
        "yet decomposed into a standalone aggregation.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_PIn")
        return EquationResult(value=value, unit="g/d", inputs_used={"Source": "Abs_PIn from shared model run"}, equation=self)
