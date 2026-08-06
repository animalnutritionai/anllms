"""
Calcium (Ca) requirement — NASEM (2021), Equations 20-373 through 20-376.

Same factorial pattern as MP maintenance: fecal endogenous (maintenance)
+ growth + gestation + lactation, summed. Each component is its own cited
knowledge object; the total composes them, mirroring
scientific/protein/mp_maintenance.py's structure.

    Fe_Ca_m (g/d) = 0.9 * Dt_DMIn                              [Eq. 20-373]
    An_Ca_g (g/d) = 9.83 * BWmature^0.22 * BW^-0.22 * BWgain    [Eq. 20-374]
    An_Ca_y (g/d) = exponential function of gestation day, BW   [Eq. 20-375]
    An_Ca_l (g/d) = (0.295 + 0.239*MilkTPp) * MilkProd          [Eq. 20-376,
                     protein-based form -- book also allows a
                     volume-based form when milk protein is unavailable,
                     not implemented here since this codebase always has
                     milk true protein available]
    An_Ca_req = Fe_Ca_m + An_Ca_g + An_Ca_y + An_Ca_l
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class CalciumMaintenanceNASEM2021(KnowledgeEquation):
    """Fecal endogenous calcium (maintenance) requirement (NASEM 2021, Eq. 20-373)."""

    name = "Calcium requirement for maintenance (fecal endogenous loss)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-373")
    variables = [Variable(symbol="Dt_DMIn", name="Dry matter intake", unit="kg/d")]
    formula_text = "Fe_Ca_m (g/d) = 0.9 * Dt_DMIn"
    assumptions = [
        "Fixed proportionality to DMI (0.9 g Ca per kg DMI) regardless of "
        "diet Ca concentration -- represents obligate fecal endogenous "
        "loss, not diet-dependent absorption loss.",
    ]
    applicability = "Adult (non-calf) dairy cattle."
    limitations = ["Does not vary by breed, age, or physiological state beyond DMI."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, dmi_kg: float) -> EquationResult:
        if dmi_kg <= 0:
            raise ValueError("dmi_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_Fe_Ca_m(An_DMIn=dmi_kg)
        return EquationResult(value=value, unit="g/d", inputs_used={"DMI (kg/d)": dmi_kg}, equation=self)


class CalciumGrowthNASEM2021(KnowledgeEquation):
    """Calcium requirement for growth (NASEM 2021, Eq. 20-374)."""

    name = "Calcium requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-374")
    variables = [
        Variable(symbol="An_BW_mature", name="Mature body weight", unit="kg"),
        Variable(symbol="An_BW", name="Current body weight", unit="kg"),
        Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d"),
    ]
    formula_text = "An_Ca_g (g/d) = 9.83 * BW_mature^0.22 * BW^-0.22 * Body_Gain"
    assumptions = [
        "Scales with the ratio of mature to current BW (animals closer to "
        "mature size deposit less Ca per unit gain, reflecting slowing "
        "skeletal mineralization with maturity).",
        "Zero when Body_Gain is zero -- this codebase's default "
        "AnimalState (frame_gain_kg_per_day=0) will make this term vanish "
        "unless explicitly set.",
    ]
    applicability = "Adult (non-calf) dairy cattle with nonzero targeted body weight gain."
    limitations = ["Empirical allometric relationship; not derived from direct skeletal Ca deposition measurement in this equation."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, bw_mature_kg: float, bw_kg: float, body_gain_kg_per_day: float) -> EquationResult:
        if bw_kg <= 0 or bw_mature_kg <= 0:
            raise ValueError("bw_kg and bw_mature_kg must be positive")
        import nasem_dairy as nd

        value = nd.calculate_An_Ca_g(An_BW_mature=bw_mature_kg, An_BW=bw_kg, Body_Gain=body_gain_kg_per_day)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"BW mature (kg)": bw_mature_kg, "BW (kg)": bw_kg, "Body gain (kg/d)": body_gain_kg_per_day},
            equation=self,
        )


class CalciumGestationNASEM2021(KnowledgeEquation):
    """Calcium requirement for gestation (NASEM 2021, Eq. 20-375)."""

    name = "Calcium requirement for gestation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-375")
    variables = [
        Variable(symbol="An_GestDay", name="Day of gestation", unit="days"),
        Variable(symbol="An_BW", name="Body weight", unit="kg"),
    ]
    formula_text = "An_Ca_y (g/d) = exponential function of gestation day, scaled by BW/715"
    assumptions = [
        "Derived from the rate of change in a modeled fetal/gravid uterine "
        "Ca accretion curve, not a constant daily amount -- requirement "
        "rises sharply in late gestation, consistent with fetal "
        "mineralization patterns.",
        "Zero at gestation_day=0 (this codebase's default for a "
        "non-pregnant cow).",
    ]
    applicability = "Pregnant dairy cattle."
    limitations = ["Scaled by a reference BW of 715 kg embedded in the coefficient; not independently re-derived here."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, gestation_day: int, bw_kg: float) -> EquationResult:
        if bw_kg <= 0:
            raise ValueError("bw_kg must be positive")
        if gestation_day < 0:
            raise ValueError("gestation_day cannot be negative")
        import nasem_dairy as nd

        value = nd.calculate_An_Ca_y(An_GestDay=gestation_day, An_BW=bw_kg)
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Gestation day": gestation_day, "BW (kg)": bw_kg},
            equation=self,
        )


class CalciumLactationNASEM2021(KnowledgeEquation):
    """Calcium requirement for lactation, protein-based form (NASEM 2021, Eq. 20-376)."""

    name = "Calcium requirement for lactation"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-376")
    variables = [
        Variable(symbol="Trg_MilkProd", name="Milk yield", unit="kg/d"),
        Variable(symbol="Trg_MilkTPp", name="Milk true protein", unit="%"),
    ]
    formula_text = "An_Ca_l (g/d) = (0.295 + 0.239 * MilkTPp) * MilkProd"
    assumptions = [
        "Uses the protein-based prediction form, matching the book's "
        "milk-true-protein regression exactly (0.295 +/- 0.73 intercept, "
        "0.239 +/- 0.029 slope per % milk true protein).",
        "The book also allows a volume-based fallback (fixed g Ca/L by "
        "breed) when milk protein data is unavailable -- not implemented "
        "here since milk true protein is always available in this "
        "codebase's MilkTarget.",
    ]
    applicability = "Lactating dairy cattle with known milk true protein percentage."
    limitations = ["Regression fit; individual cows can deviate from this average relationship."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(self, milk_yield_kg: float, milk_true_protein_pct: float) -> EquationResult:
        if milk_yield_kg < 0:
            raise ValueError("milk_yield_kg cannot be negative")
        import nasem_dairy as nd
        from anllms.scientific.protein.milk_net_protein import MilkNetProteinNASEM2021

        # Mlk_NP_g only gates which branch this function uses (protein-based
        # vs volume-based); the branch it selects does not use its VALUE.
        # We still compute the real figure via our own tested equation
        # rather than passing an arbitrary placeholder, so nothing here
        # is a made-up number even where it's not strictly load-bearing.
        mlk_np_g = MilkNetProteinNASEM2021().calculate(
            milk_yield_kg=milk_yield_kg, milk_true_protein_pct=milk_true_protein_pct
        ).value

        value = nd.calculate_An_Ca_l(
            Mlk_NP_g=mlk_np_g, Ca_Mlk=3.8,
            Trg_MilkProd=milk_yield_kg, Trg_MilkTPp=milk_true_protein_pct,
        )
        return EquationResult(
            value=value, unit="g/d",
            inputs_used={"Milk yield (kg/d)": milk_yield_kg, "Milk true protein (%)": milk_true_protein_pct},
            equation=self,
        )


class CalciumRequirementNASEM2021(KnowledgeEquation):
    """Total calcium requirement (NASEM 2021): maintenance + growth + gestation + lactation."""

    name = "Total calcium (Ca) requirement"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Sum of Equations 20-373, 20-374, 20-375, 20-376",
    )
    variables = [
        Variable(symbol="Fe_Ca_m", name="Maintenance Ca", unit="g/d"),
        Variable(symbol="An_Ca_g", name="Growth Ca", unit="g/d"),
        Variable(symbol="An_Ca_y", name="Gestation Ca", unit="g/d"),
        Variable(symbol="An_Ca_l", name="Lactation Ca", unit="g/d"),
    ]
    formula_text = "An_Ca_req = Fe_Ca_m + An_Ca_g + An_Ca_y + An_Ca_l"
    assumptions = ["Applies to adult (non-calf) cattle; calves use a separate combined equation (Eq. 20-372) not implemented here."]
    applicability = "Adult dairy cattle: dry, lactating, and/or pregnant."
    limitations = ["Inherits all limitations of its four components."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE

    def calculate(
        self, dmi_kg: float, bw_mature_kg: float, bw_kg: float,
        body_gain_kg_per_day: float, gestation_day: int,
        milk_yield_kg: float, milk_true_protein_pct: float,
    ) -> EquationResult:
        maintenance = CalciumMaintenanceNASEM2021().calculate(dmi_kg=dmi_kg)
        growth = CalciumGrowthNASEM2021().calculate(
            bw_mature_kg=bw_mature_kg, bw_kg=bw_kg, body_gain_kg_per_day=body_gain_kg_per_day
        )
        gestation = CalciumGestationNASEM2021().calculate(gestation_day=gestation_day, bw_kg=bw_kg)
        lactation = CalciumLactationNASEM2021().calculate(
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


class CalciumSupplyNASEM2021(KnowledgeEquation):
    """Absorbed calcium supply from the diet (NASEM 2021, Eq. 20-370/20-371)."""

    name = "Absorbed calcium (Ca) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-370, 20-371")
    variables = [
        Variable(symbol="Fd_CaInf", name="Calcium intake per ingredient", unit="g/d"),
        Variable(symbol="Fd_acCaf", name="Absorption coefficient per ingredient", unit="g/g"),
    ]
    formula_text = "Fd_absCaInf = Fd_CaInf * Fd_acCaf; Abs_CaIn = sum(Fd_absCaInf) across ration"
    assumptions = [
        "Absorption coefficient (AC) is a per-INGREDIENT value from the "
        "real feed library (Fd_acCa), not a single dietary average -- the "
        "book states this replaced NRC (2001)'s single-average approach "
        "specifically because Ca availability varies widely between "
        "forages and mineral supplements.",
        "For adult (non-calf) cattle, the feed-library value is used "
        "as-is with no further adjustment.",
    ]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed from per-ingredient feed data -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "This equation extracts Abs_CaIn from a full nasem_dairy model "
        "run (the same run shared with DMI/requirement/other supply "
        "calculations in RequirementsReport) rather than independently "
        "summing Fd_CaInf x Fd_acCaf per ingredient in this codebase. "
        "The FORMULA and citation are confirmed correct against the "
        "primary text; the computation itself is not yet decomposed into "
        "a standalone per-ingredient aggregation the way Ration.to_diet() "
        "does for NDF/ADF.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_CaIn")
        return EquationResult(value=value, unit="g/d", inputs_used={"Source": "Abs_CaIn from shared model run"}, equation=self)
