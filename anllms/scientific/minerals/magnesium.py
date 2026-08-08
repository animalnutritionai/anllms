"""
Magnesium (Mg) requirement — NASEM (2021), Equations 20-398 through 20-404.

Simpler than calcium/phosphorus: no allometric BW-scaling terms, and
gestation Mg is a STEP FUNCTION (zero until day 190, then a fixed
BW-scaled amount) rather than a continuous exponential curve.

    Ur_Mg_m (g/d) = 0.0007 * BW                          [Eq. 20-398]
    Fe_Mg_m (g/d) = 0.3 * Dt_DMIn                         [Eq. 20-399]
    An_Mg_m (g/d) = Ur_Mg_m + Fe_Mg_m                     [Eq. 20-400]
    An_Mg_g (g/d) = 0.45 * Body_Gain                      [Eq. 20-401]
    An_Mg_y (g/d) = 0 if GestDay<=190, else 0.3*(BW/715)  [Eq. 20-402]
    An_Mg_l (g/d) = 0.11 * MilkProd                       [Eq. 20-403]
    An_Mg_req = An_Mg_m + An_Mg_g + An_Mg_y + An_Mg_l     [Eq. 20-404]

NOTE on equation numbering (RESOLVED by structural cross-reference, not by
a direct paginated-book read): the source document's text extraction has
gaps in this section -- formulas for several equations (An_Mg_g, An_Mg_y,
An_Mg_req) didn't extract as text, likely because they were images/tables
in the original PDF, the same failure mode seen for phosphorus's Eq.
20-385 and 20-391 immediately above this section in the same document.
The raw extraction also shows two spurious duplicate "(Equation 20-402)"
labels and a duplicated An_Mg_m formula attached to both 20-400 and
20-401 -- but the analogous Calcium and Phosphorus sections (Eq. 20-370
through 20-394), which have the SAME missing-formula problem, show ZERO
duplicate equation numbers: every number is distinct and sequential, one
per equation, even when its formula text is missing. This strongly
suggests the Magnesium duplicates are an extraction artifact, not a real
book duplication.

Cross-checking the reference software's function order in
micronutrient_requirement.py (Ur_Mg_m -> Fe_Mg_m -> An_Mg_m -> An_Mg_g ->
An_Mg_y -> An_Mg_l -> An_Mg_req -> An_Mg_bal -> An_Mg_prod) confirms
one-equation-per-slot mapping, matching the same pattern independently
verified for phosphorus (where the software's An_P_req function
corresponds to the book's own text-missing Eq. 20-391). Applying that
pattern here resolves the numbering as: An_Mg_m=20-400, An_Mg_g=20-401,
An_Mg_y=20-402, An_Mg_l=20-403 (already had visible text confirming this
one), An_Mg_req=20-404, An_Mg_bal=20-405 and An_Mg_prod=20-406 (both
confirmed directly, formula text visible in the extraction).

This is a HIGH-CONFIDENCE RECONSTRUCTION, not a direct citation read off
a paginated copy of the book -- flagged as such in each equation's
known_discrepancies below. A paginated-copy spot-check remains the
gold-standard confirmation if one becomes available.
"""

from __future__ import annotations

from anllms.knowledge.models import Citation, EquationResult, KnowledgeEquation, Variable
from anllms.knowledge.publications import NASEM_DAIRY_2021, NASEM_DAIRY_2021_SOFTWARE


class MagnesiumMaintenanceNASEM2021(KnowledgeEquation):
    """Magnesium requirement for maintenance: urinary + fecal (NASEM 2021, Eq. 20-398 to 20-401)."""

    name = "Magnesium requirement for maintenance (urinary + fecal)"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equations 20-398, 20-399, 20-400")
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
    """Magnesium requirement for growth (NASEM 2021, Eq. 20-401)."""

    name = "Magnesium requirement for growth"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20", equation_number="Equation 20-401")
    variables = [Variable(symbol="Body_Gain", name="Body weight gain", unit="kg/d")]
    formula_text = "An_Mg_g (g/d) = 0.45 * Body_Gain"
    assumptions = ["Simple linear relationship, no BW-scaling term (unlike Ca/P growth equations)."]
    applicability = "Cattle with nonzero targeted body weight gain."
    limitations = ["Equation number resolved by structural cross-reference, not a direct paginated-book read -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "This equation's formula text did not extract from the source "
        "document (likely an image/table in the original PDF). Its number "
        "was resolved by cross-referencing the analogous, unambiguous "
        "Calcium/Phosphorus sections (which show the same missing-formula "
        "pattern but zero duplicate equation numbers) and the reference "
        "software's function ordering (Ur_Mg_m, Fe_Mg_m, An_Mg_m, An_Mg_g, "
        "An_Mg_y, An_Mg_l, An_Mg_req, An_Mg_bal, An_Mg_prod). Previously "
        "cited as Eq. 20-402; corrected to 20-401 on this basis. A "
        "paginated-copy spot-check would still be the gold-standard "
        "confirmation.",
    ]

    def calculate(self, body_gain_kg_per_day: float) -> EquationResult:
        import nasem_dairy as nd

        value = nd.calculate_An_Mg_g(Body_Gain=body_gain_kg_per_day)
        return EquationResult(value=value, unit="g/d", inputs_used={"Body gain (kg/d)": body_gain_kg_per_day}, equation=self)


class MagnesiumGestationNASEM2021(KnowledgeEquation):
    """Magnesium requirement for gestation -- a step function (NASEM 2021, Eq. 20-402)."""

    name = "Magnesium requirement for gestation"
    citation = Citation(
        publication=NASEM_DAIRY_2021, chapter="6/20",
        equation_number="Equation 20-402 (resolved by structural cross-reference -- see known_discrepancies)",
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
    limitations = ["Equation number resolved by structural cross-reference, not a direct paginated-book read -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "This equation's formula text did not extract from the source "
        "document (likely an image/table in the original PDF), and the "
        "raw extraction showed two spurious duplicate '(Equation 20-402)' "
        "labels with no formula between them, previously logged as an "
        "unresolved citation gap. Resolution: the analogous Calcium and "
        "Phosphorus sections in the same document (Eq. 20-370 to 20-394) "
        "show the identical missing-formula problem but ZERO duplicate "
        "equation numbers -- every number there is distinct and "
        "sequential even when its formula didn't extract. Cross-checking "
        "the reference software's function order (Ur_Mg_m, Fe_Mg_m, "
        "An_Mg_m, An_Mg_g, An_Mg_y, An_Mg_l, An_Mg_req, An_Mg_bal, "
        "An_Mg_prod) against that one-equation-per-slot pattern gives "
        "An_Mg_g=20-401 and An_Mg_y=20-402. The FORMULA and its "
        "step-function behavior were already confirmed against the "
        "reference software and real fixture test data; this resolves "
        "the citation number too, but by structural inference rather "
        "than a direct paginated-book read. A paginated-copy spot-check "
        "would still be the gold-standard confirmation if one becomes "
        "available.",
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
        equation_number="Sum of Equations 20-400 (maintenance), 20-401 (growth), 20-402 (gestation), "
                         "20-403 (lactation); the sum itself corresponds to Eq. 20-404, whose formula "
                         "text was not independently re-derived here",
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
    limitations = [
        "Growth and gestation component equation numbers (20-401, 20-402) were resolved by "
        "structural cross-reference rather than a direct paginated-book read -- see each "
        "component's own known_discrepancies.",
    ]
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


class MagnesiumSupplyNASEM2021(KnowledgeEquation):
    """Absorbed magnesium supply from the diet (NASEM 2021, Eq. 20-395/20-396)."""

    name = "Absorbed magnesium (Mg) supply from the diet"
    citation = Citation(publication=NASEM_DAIRY_2021, chapter="6/20 (see also Chapter 7)", equation_number="Equations 20-395, 20-396")
    variables = [
        Variable(symbol="Dt_K", name="Dietary potassium concentration", unit="% of DM"),
        Variable(symbol="Dt_MgIn", name="Dietary magnesium intake", unit="g/d"),
    ]
    formula_text = "Abs_MgIn = Dt_acMg * Dt_MgIn, where Dt_acMg is a DIET-LEVEL (not per-ingredient) coefficient depending on Dt_K"
    assumptions = [
        "UNLIKE every other mineral in this codebase (Ca, P, Na, Cl, K, "
        "Co, Cu, Fe, Mn, Zn), magnesium absorption is NOT a simple "
        "per-ingredient lookup -- it is a single diet-level coefficient "
        "that DECREASES as dietary potassium increases (Mg absorption is "
        "inhibited by K, per the book's own explicit statement). This is "
        "a real, distinctive physiological interaction, not a "
        "simplification.",
    ]
    applicability = "Any lactating dairy cow diet."
    limitations = ["Extracted from a full reference-model run rather than independently recomputed -- see known_discrepancies."]
    software_reference = NASEM_DAIRY_2021_SOFTWARE
    known_discrepancies = [
        "Extracts Abs_MgIn from a full nasem_dairy model run rather than "
        "independently computing Dt_acMg from Dt_K in this codebase. "
        "Formula/citation confirmed correct against the primary text.",
    ]

    def calculate(self, model_output) -> EquationResult:
        value = model_output.get_value("Abs_MgIn")
        return EquationResult(value=value, unit="g/d", inputs_used={"Source": "Abs_MgIn from shared model run"}, equation=self)
