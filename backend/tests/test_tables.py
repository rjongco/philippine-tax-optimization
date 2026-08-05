"""Bracket boundary behaviour for the two statutory tables."""

from decimal import Decimal

import pytest

from app.engine.money import dec
from app.engine.tables import annual_income_tax, sss_employee_share


@pytest.mark.parametrize(
    "taxable,expected",
    [
        ("0", "0"),
        ("249999.99", "0"),
        ("250000", "0"),            # top of the zero bracket
        ("250100", "15"),           # 100 into the 15% band
        ("400000", "22500"),        # base tax at the boundary, no excess
        ("400100", "22520"),
        ("800000", "102500"),
        ("2000000", "402500"),
        ("8000000", "2202500"),
        ("9000000", "2552500"),     # 2,202,500 + 1,000,000 * 35%
    ],
)
def test_train_brackets(taxable, expected):
    assert annual_income_tax(dec(taxable)) == dec(expected)


def test_train_is_zero_for_negative_input():
    assert annual_income_tax(dec("-50000")) == dec("0")


def test_train_is_continuous_at_every_boundary():
    """No jump discontinuity: one centavo more must not cost more than a centavo."""
    for bound in ["250000", "400000", "800000", "2000000", "8000000"]:
        at = annual_income_tax(dec(bound))
        just_after = annual_income_tax(dec(bound) + dec("0.01"))
        assert just_after - at < dec("0.01")


@pytest.mark.parametrize(
    "compensation,expected",
    [
        ("0", "250"),
        ("5000", "250"),
        ("5250", "275"),            # first step
        ("5749.99", "275"),
        ("5750", "300"),
        ("20000", "1000"),
        ("34749.99", "1725"),
        ("34750", "1750"),          # MSC ceiling
        ("100000", "1750"),         # flat above the ceiling
        ("1000000", "1750"),
    ],
)
def test_sss_brackets(compensation, expected):
    assert sss_employee_share(dec(compensation)) == dec(expected)


def test_sss_is_monotonic_non_decreasing():
    previous = Decimal("-1")
    for step in range(0, 40000, 250):
        current = sss_employee_share(dec(str(step)))
        assert current >= previous
        previous = current


def test_sss_never_exceeds_the_employee_cap():
    for step in range(0, 200000, 1000):
        assert sss_employee_share(dec(str(step))) <= dec("1750")
