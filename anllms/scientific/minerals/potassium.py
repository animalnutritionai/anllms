"""
Potassium (K) requirement — NASEM (2021), Equations 20-430 through 20-435.

Unlike sodium/chlorine, potassium maintenance has BOTH a urinary and
fecal term, and the urinary term depends on whether the cow is lactating:

    Ur_K_m (g/d) = 0.2*BW if lactating (MilkProd>0), else 0.07*BW  [Eq. 20-430]
    Fe_K_m (g/d) = 2.5 * Dt_DMIn                           [Eq. 20-431]
    An_K_m (g/d) = Ur_K_m + Fe_K_m                          [Eq. 20-432]
    An_K_g (g/d) = 2.5 * Body_Gain                          [Eq. 20-433]
    An_K_y (g/d) = 0 if GestDay<=190, else 1.03*(BW/715)    [Eq. 20-434]
    An_K_l (g/d) = 1.5 * MilkProd                           [Eq. 20-435]
    An_K_req = An_K_m + An_K_g + An_K_y + An_K_l

EQUATION NUMBER: Confirmed directly from a paginated copy of the book
(user-provided screenshot, Aug 2026) -- Ur_K_m is Equation 20-430, sitting
between An_K_Clf (20-429) and Fe_K_m (20-431). Previously cited only as
"not separately numbered"; that hedge is now resolved.

KNOWN DISCREPANCY -- coefficient direction (book text vs. reference
software): the paginated screenshot's criteria table appears to read
">0 kg/d milk -> 0.07*BW" and "0 kg/d milk -> 0.2*BW" -- the OPPOSITE
direction from what `nasem_dairy`'s calculate_Ur_K_m() implements
(0.2*BW when lactating, 0.07*BW when dry), which is also what this
module's formula and the code below use. Per project decision, the
reference software is treated as correct here, following NASEM's own
stated precedence for exactly this kind of conflict (Ch. 20 model
description, "Nutrient Supply Model" intro):

    "Should there be differences between the description of the model
    herein and the actual model code written in R, the latter is more
    likely to be correct, and the difference reflects a mistake in the
    transcription. The R code was developed and verified over a 4-year
    period and thus should generally be the more reliable source,
    although mistakes are certainly possible."
    -- NASEM (2021), Nutrient Requirements of Dairy Cattle, 8th Rev. Ed.,
    Ch. 20, "Nutrient Supply Model" (model description introduction)

This is documented in known_discrepancies below (and therefore surfaced
to end users via explain()) rather than silently picked one way. A
second, clearer paginated read of that specific cell would still be
useful to confirm the screenshot wasn't misread, but does not change
which value the platform calculates.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class PotassiumMaintenanceNASEM2021(KnowledgeEquation):
    """Potassium requirement for maintenance: urinary (lactation-dependent) + fecal (NASEM 2021, Eq. 20-430/20-431/20-432)."""

    name = "Potassium requirement for maintenance (urinary + fecal)"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Equation 20-430 (Ur_K_m, confirmed by direct paginated read), "
                         "Equation 20-431 (Fe_K_m), Equation 20-432 (An_K_m sum)",
    )
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
        "considerably higher than the AI for dry cows/growing heifers. "
        "This direction matches the reference software; see "
        "known_discrepancies for a possible book-text vs. software "
        "conflict on which coefficient applies to which case.",
        "Uses milk PRODUCTION (>0) as the lactating/non-lactating switch, "
        "not a separate physiological-state flag.",
    ]
    applicability = "Adult (non-calf) dairy cattle, lactating or dry."
    limitations = [
        "The book's own criteria table for Ur_K_m (Eq. 20-430), as read "
        "from a paginated screenshot, appears to assign 0.07*BW to "
        "lactating cows and 0.2*BW to dry cows -- the reverse of what "
        "the reference software calculates. This platform follows the "
        "software. See known_discrepancies for the full explanation and "
        "the NASEM committee's own stated precedence for this situation.",
    ]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Possible book-text vs. reference-software conflict on the "
        "Ur_K_m (Eq. 20-430) coefficient assignment: a user-provided "
        "paginated screenshot of the book's criteria table appears to "
        "read '>0 kg/d milk -> 0.07*BW' and '0 kg/d milk -> 0.2*BW', "
        "the opposite of nasem_dairy's calculate_Ur_K_m() (0.2*BW when "
        "lactating, 0.07*BW when dry). This platform calculates using "
        "the software's direction, per NASEM's own stated precedence "
        "for such conflicts (Ch. 20, 'Nutrient Supply Model' intro): "
        "\"Should there be differences between the description of the "
        "model herein and the actual model code written in R, the "
        "latter is more likely to be correct, and the difference "
        "reflects a mistake in the transcription. The R code was "
        "developed and verified over a 4-year period and thus should "
        "generally be the more reliable source, although mistakes are "
        "certainly possible.\" Not silently resolved -- flagged here "
        "per project scientific-integrity rules. A second, clearer "
        "paginated read of that specific table cell would still be "
        "useful confirmation, though it would not change the computed "
        "result either way.",
    ]

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


class PotassiumSupplyNASEM2021(KnowledgeEquation):
    """Absorbed potassium supply from the diet (NASEM 2021, Eq. 20-427/20-428)."""

    name = "Absorbed potassium (K) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-427, 20-428")
    variables = [
        Variable(symbol="Fd_KInf", name="Potassium intake per ingredient", unit="g/d"),
        Variable(symbol="Fd_acKf", name="Absorption coefficient per ingredient", unit="g/g"),
    ]
    formula_text = "Fd_absKInf = Fd_KInf * Fd_acKf; Abs_KIn = sum(Fd_absKInf) across ration"
    assumptions = ["Per-ingredient absorption coefficient from the real feed library."]
    applicability = "Any lactating dairy cow diet with real feed library ingredients."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_KIn from a full nasem_dairy model run rather than "
        "independently summing per-ingredient contributions in this codebase.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_KIn")
        return EquationResult(value=value, unit="g/d", inputs_used={"Source": "Abs_KIn from shared model run"}, equation=self)
