"""The hard invariants from PAYROLL_MODEL.md section 10.

A change that breaks one of these is a bug, not a tuning decision.
"""

from dataclasses import replace
from decimal import Decimal

import pytest

from app.defaults import default_scenario
from app.engine import compute
from app.engine.money import dec

ZERO = dec(0)


@pytest.fixture(scope="module")
def result():
    return compute(default_scenario())


def test_structure_balances_for_every_employee(result):
    """D + A + B = G. Monthly take-home must equal signed gross."""
    for b in result.breakdowns:
        assert (
            b.deminimis_monthly + b.incentive_monthly + b.basic_monthly
            == b.signed_gross_monthly
        ), b.name
        assert b.invariants.structure_balances, b.name


def test_no_minimum_wage_breach(result):
    for b in result.breakdowns:
        assert b.invariants.minimum_wage_ok, f"{b.name} at {b.daily_rate}/day"


def test_thirteenth_month_payment_covers_the_statutory_amount(result):
    """P >= B — the December payment must cover one month of basic."""
    for b in result.breakdowns:
        assert b.thirteenth_month_payment >= b.basic_monthly, b.name


def test_non_restructured_employees_are_held_harmless(result):
    """Never worse off. Better off is allowed and, under RR 29-2025, expected.

    The rule is `incentive = cash_anchor - de_minimis`, clamped at zero. Now that
    de minimis (6,399.99) exceeds the anchor (5,300) the clamp binds, so these
    employees land below the old baseline rather than exactly on it.
    """
    for b in result.breakdowns:
        if not b.restructure:
            assert b.tax_saved_annual >= ZERO, b.name
            assert b.incentive_monthly >= ZERO, b.name
            assert b.invariants.held_harmless is True, b.name


def test_no_employee_is_worse_off(result):
    for b in result.breakdowns:
        assert b.tax_saved_annual >= ZERO, f"{b.name} loses {b.tax_saved_annual}"


def test_deminimis_is_within_statutory_cap():
    for item in default_scenario().deminimis_items:
        assert not item.over_cap, item.label


# --- regression: the hold-harmless bug -------------------------------------
# Column G formerly hardcoded the baseline award into its "No" branch. That was
# correct only while de minimis 4,300 + award 1,000 happened to equal the 5,300
# cash anchor. Changing the schedule silently pushed the four untouched employees
# into tax. The fix ties the No branch to `cash_anchor - deminimis` instead.


@pytest.mark.parametrize("drop", ["416.67", "833.33", "1250.00", "2000.00"])
def test_hold_harmless_survives_a_deminimis_change(drop):
    """Removing any item must not move a non-restructured employee's tax."""
    scenario = default_scenario()
    reduced = [
        replace(i, granted_monthly=i.granted_monthly - dec(drop))
        if i.key == "rice"
        else i
        for i in scenario.deminimis_items
    ]
    changed = compute(replace(scenario, deminimis_items=reduced))

    for b in changed.breakdowns:
        if not b.restructure:
            assert b.tax_saved_annual >= ZERO, (
                f"{b.name} lost {b.tax_saved_annual} after de minimis fell by {drop}"
            )
            assert b.incentive_monthly >= ZERO, b.name
            # Never above the baseline: taxable basic may fall, never rise.
            assert b.basic_monthly <= b.baseline_basic_monthly, b.name


def test_hold_harmless_holds_when_deminimis_is_zero():
    """The degenerate case: no de minimis at all."""
    scenario = default_scenario()
    stripped = [replace(i, granted_monthly=ZERO) for i in scenario.deminimis_items]
    changed = compute(replace(scenario, deminimis_items=stripped))

    assert changed.deminimis_monthly == ZERO
    for b in changed.breakdowns:
        if not b.restructure:
            assert b.tax_saved_annual == ZERO, b.name


# --- generated inputs ------------------------------------------------------


@pytest.mark.parametrize("gross", [str(g) for g in range(20000, 160000, 7000)])
def test_structure_balances_across_the_salary_range(gross):
    from app.engine.models import Employee

    scenario = default_scenario()
    probe = Employee(id="probe", name="Probe", signed_gross_monthly=dec(gross))
    changed = compute(replace(scenario, employees=[probe]))
    b = changed.breakdowns[0]

    assert b.deminimis_monthly + b.incentive_monthly + b.basic_monthly == dec(gross)
    assert b.incentive_monthly >= ZERO
    assert b.spill_annual >= ZERO
    assert b.bir_benefits_annual <= dec("90000")


@pytest.mark.parametrize("gross", ["20000", "35000", "60000", "100000", "150000"])
def test_exempt_total_never_exceeds_the_legal_maximum(gross):
    """12 x de minimis + 90,000 is the ceiling. Nothing may exceed it."""
    from app.engine.models import Employee

    scenario = default_scenario()
    probe = Employee(id="probe", name="Probe", signed_gross_monthly=dec(gross))
    changed = compute(replace(scenario, employees=[probe]))
    b = changed.breakdowns[0]

    maximum = changed.deminimis_monthly * dec(12) + dec("90000")
    assert b.total_exempt_annual <= maximum
