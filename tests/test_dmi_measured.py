"""
Tests for MeasuredDMINASEM2021 -- the caller-supplied (measured/estimated)
DMI path, the "actual" half of the DMI actual-vs-predicted dual-mode
decision. Unlike the predictive equations, there is no regression fixture
to validate against here: this equation object is an identity wrapper
around a caller-supplied number, so these tests check pass-through
correctness, input validation, and that explain() surfaces the right
framing rather than checking a formula result.
"""

import pytest

from anllms.scientific.energy.dmi_measured import MeasuredDMINASEM2021


def test_measured_dmi_passes_value_through_unchanged():
    result = MeasuredDMINASEM2021().calculate(dmi_kg=24.5)
    assert result.value == 24.5
    assert result.unit == "kg/d"


def test_measured_dmi_rejects_zero():
    with pytest.raises(ValueError):
        MeasuredDMINASEM2021().calculate(dmi_kg=0)


def test_measured_dmi_rejects_negative():
    with pytest.raises(ValueError):
        MeasuredDMINASEM2021().calculate(dmi_kg=-5)


def test_measured_dmi_inputs_used_labeled_as_caller_supplied():
    result = MeasuredDMINASEM2021().calculate(dmi_kg=24.5)
    assert any("supplied directly by caller" in k for k in result.inputs_used)


def test_measured_dmi_explanation_does_not_claim_a_numbered_equation():
    result = MeasuredDMINASEM2021().calculate(dmi_kg=24.5)
    explanation = result.explain()
    # Must not claim a numbered book equation drove this value.
    assert "Equation 2-1" not in explanation
    assert "Equation 2-2" not in explanation
    # Must be honest that this is the DMIn_eqn == 0 pass-through mode.
    assert "DMIn_eqn == 0" in explanation
