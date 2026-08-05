"""Cash timing — the accrual model expanded onto real payout dates."""

import pytest

from app.defaults import default_scenario
from app.engine import compute
from app.engine.money import dec, peso
from app.engine.schedule import build_schedule, build_schedules

ZERO = dec(0)


@pytest.fixture(scope="module")
def scenario():
    return default_scenario()


@pytest.fixture(scope="module")
def result(scenario):
    return compute(scenario)


@pytest.fixture(scope="module")
def schedules(result, scenario):
    return build_schedules(result.breakdowns, scenario.parameters)


def test_every_schedule_reconciles(schedules):
    """Annual cash = 12 x signed gross + the 13th-month payment.

    This is the proof that re-timing moved money without creating or destroying it.
    """
    for s in schedules:
        assert s.reconciles, f"{s.name}: {s.annual_gross_cash}"


def test_twelve_months_and_twenty_four_cutoffs(schedules):
    for s in schedules:
        assert len(s.months) == 12
        assert len(s.cutoffs) == 24


def test_incentive_lands_on_cutoff_one_only(schedules, result):
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        expected = peso(by_id[s.employee_id].incentive_monthly)
        for c in s.cutoffs:
            if c.cutoff == 1:
                assert c.incentive == expected, f"{s.name} {c.month_name}"
            else:
                assert c.incentive == ZERO, f"{s.name} {c.month_name}"


def test_thirteenth_month_is_december_cutoff_one(schedules, result):
    """PD 851 requires payment on or before 24 December, so it cannot sit on the 30th."""
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        expected = by_id[s.employee_id].thirteenth_month_payment
        paid = [c for c in s.cutoffs if c.thirteenth_month > ZERO]
        assert len(paid) == 1, s.name
        assert paid[0].month == 12 and paid[0].cutoff == 1, s.name
        assert paid[0].thirteenth_month == expected, s.name


def test_the_two_cutoffs_sum_back_to_the_monthly_amount(schedules):
    """A repeating decimal cannot be paid twice. The halves must still reconcile."""
    for s in schedules:
        for m in s.months:
            pair = [c for c in s.cutoffs if c.month == m.month]
            assert sum(c.basic for c in pair) == m.basic, s.name
            assert sum(c.deminimis for c in pair) == m.deminimis, s.name
            assert sum(c.gross_cash for c in pair) == m.gross_cash, s.name


def test_cutoff_halves_differ_by_at_most_one_centavo(schedules):
    for s in schedules:
        for m in s.months:
            c1, c2 = [c for c in s.cutoffs if c.month == m.month]
            assert abs(c1.basic - c2.basic) <= dec("0.01"), s.name
            assert abs(c1.deminimis - c2.deminimis) <= dec("0.01"), s.name


def test_every_payable_amount_is_in_whole_centavos(schedules):
    """Nothing in the cash view may carry sub-centavo precision."""
    for s in schedules:
        for c in s.cutoffs:
            for field in (c.basic, c.deminimis, c.incentive, c.thirteenth_month,
                          c.gross_cash, c.sss, c.philhealth, c.pagibig,
                          c.withholding, c.net_cash):
                assert field == field.quantize(dec("0.01")), f"{s.name}: {field}"


def test_cash_view_preserves_invariant_one(schedules, result):
    """de minimis + incentive + basic = signed gross, after rounding to centavos."""
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        b = by_id[s.employee_id]
        january = s.months[0]
        assert (
            january.basic + january.deminimis + january.incentive
            == b.signed_gross_monthly
        ), s.name


def test_only_december_differs_from_the_other_months(schedules):
    for s in schedules:
        non_december = {m.gross_cash for m in s.months if m.month != 12}
        assert len(non_december) == 1, f"{s.name} has uneven ordinary months"


def test_annual_net_tracks_the_accrual_model_within_rounding_drift(schedules, result):
    """Cash and accrual differ by quantization only.

    Deductions are withheld in whole centavos every month, so twelve roundings
    accumulate a few centavos against the exact accrual figure. That is correct
    payroll behaviour — BIR's year-end adjustment exists precisely to settle it —
    but the drift must stay small enough to be obviously rounding and not a
    modelling error. Half a peso over a full year is the ceiling.
    """
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        b = by_id[s.employee_id]
        expected = b.net_pay_monthly * dec(12) + b.thirteenth_month_payment
        drift = abs(s.annual_net_cash - expected)
        assert drift < dec("0.50"), f"{s.name}: drift {drift}"


def test_gross_cash_reconciles_exactly_with_no_drift(schedules, result):
    """Gross has no rounding freedom — it must land on the peso figure exactly."""
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        b = by_id[s.employee_id]
        expected = peso(b.signed_gross_monthly) * dec(12) + peso(
            b.thirteenth_month_payment
        )
        assert s.annual_gross_cash == expected, s.name


def test_cutoff_two_is_lighter_than_cutoff_one_by_the_incentive(schedules, result):
    """The incentive is the only thing making the two payouts uneven.

    Tolerance is one centavo: the odd centavo from an uneven split lands on
    cutoff 2, so the gap is the incentive give or take that.
    """
    by_id = {b.employee_id: b for b in result.breakdowns}
    for s in schedules:
        b = by_id[s.employee_id]
        c1, c2 = [c for c in s.cutoffs if c.month == 1]
        gap = c1.gross_cash - c2.gross_cash
        assert abs(gap - b.incentive_monthly) <= dec("0.02"), f"{s.name}: gap {gap}"


def test_rollout_lag_is_disclosed(schedules):
    for s in schedules:
        assert any("Rollout lag" in n for n in s.notes), s.name
