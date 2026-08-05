"""Cash timing — turning the annual accrual model into actual payout dates.

The model in compute.py is an ACCRUAL view: it says what each component is worth per
month. A payroll register is a CASH view: it says what leaves the bank on a date.
They are not the same object, which is why this module exists rather than the UI
dividing monthly figures by two.

Settled cadence (design doc section 9):

  taxable basic        half on each cutoff
  de minimis           half on each cutoff — all six items are paid as monthly cash
  incentive            cutoff 1, for the PREVIOUS month's determination
  13th-month payment   December, cutoff 1 (PD 851 requires on or before 24 December)

The incentive lands on the following month's first cutoff so the determination
required by PAYROLL_MODEL.md section 10 gets a full pay period. An approver signing
under month-end time pressure is how determinations become rubber stamps, and the
exemption depends on the determination being genuine.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List

from .models import Breakdown, Parameters
from .money import TWELVE, dec, peso

ZERO = dec(0)
TWO = dec(2)
DECEMBER = 12

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


@dataclass(frozen=True)
class CutoffLine:
    """One payout date."""

    month: int
    month_name: str
    cutoff: int              # 1 = 15th, 2 = 30th
    basic: Decimal
    deminimis: Decimal
    incentive: Decimal
    thirteenth_month: Decimal
    gross_cash: Decimal
    sss: Decimal
    philhealth: Decimal
    pagibig: Decimal
    withholding: Decimal
    net_cash: Decimal
    note: str = ""


@dataclass(frozen=True)
class MonthLine:
    month: int
    month_name: str
    basic: Decimal
    deminimis: Decimal
    incentive: Decimal
    thirteenth_month: Decimal
    gross_cash: Decimal
    deductions: Decimal
    net_cash: Decimal


@dataclass(frozen=True)
class EmployeeSchedule:
    employee_id: str
    name: str
    months: List[MonthLine]
    cutoffs: List[CutoffLine]
    annual_gross_cash: Decimal
    annual_net_cash: Decimal
    reconciles: bool
    notes: List[str]


def _split(total: Decimal) -> tuple:
    """Split a payable amount into two halves that sum back to it exactly.

    The accrual model carries repeating decimals — a basic salary of 23,508.33...
    cannot be paid, and half of it cannot be paid twice. Round the half and give the
    remainder to the second cutoff, so the two payouts always reconcile to the
    monthly figure with no drifting centavo.
    """
    first = peso(total / TWO)
    return first, total - first


def build_schedule(b: Breakdown, p: Parameters) -> EmployeeSchedule:
    """Expand one employee's annual model into 12 months and 24 cutoffs.

    Components are quantized to centavos here, because this is the cash view. De
    minimis and the incentive are rounded directly; basic salary takes the residual
    so that de minimis + incentive + basic still equals signed gross exactly, which
    is invariant 1 and must survive the move from accrual to cash.
    """
    gross_pay = peso(b.signed_gross_monthly)
    dm_pay = peso(b.deminimis_monthly)
    incentive_pay = peso(b.incentive_monthly)
    basic_pay = gross_pay - dm_pay - incentive_pay
    thirteenth_pay = peso(b.thirteenth_month_payment)

    basic_c1, basic_c2 = _split(basic_pay)
    dm_c1, dm_c2 = _split(dm_pay)
    sss_c1, sss_c2 = _split(peso(b.sss_employee))
    phic_c1, phic_c2 = _split(peso(b.philhealth_employee))
    hdmf_c1, hdmf_c2 = _split(peso(b.pagibig_employee))
    wtax_c1, wtax_c2 = _split(peso(b.withholding_monthly))

    cutoffs: List[CutoffLine] = []
    months: List[MonthLine] = []

    for m in range(1, 13):
        thirteenth = thirteenth_pay if m == DECEMBER else ZERO

        # cutoff 1 — carries the incentive earned the previous month, plus the
        # 13th-month payment in December (before the 24th, per PD 851)
        c1_gross = basic_c1 + dm_c1 + incentive_pay + thirteenth
        c1_ded = sss_c1 + phic_c1 + hdmf_c1 + wtax_c1
        cutoffs.append(
            CutoffLine(
                month=m,
                month_name=MONTHS[m - 1],
                cutoff=1,
                basic=basic_c1,
                deminimis=dm_c1,
                incentive=incentive_pay,
                thirteenth_month=thirteenth,
                gross_cash=c1_gross,
                sss=sss_c1,
                philhealth=phic_c1,
                pagibig=hdmf_c1,
                withholding=wtax_c1,
                net_cash=c1_gross - c1_ded,
                note=(
                    "Incentive for "
                    f"{MONTHS[(m - 2) % 12]}, released after determination."
                    + (" 13th-month payment included." if thirteenth else "")
                ),
            )
        )

        # cutoff 2 — basic and de minimis only
        c2_gross = basic_c2 + dm_c2
        c2_ded = sss_c2 + phic_c2 + hdmf_c2 + wtax_c2
        cutoffs.append(
            CutoffLine(
                month=m,
                month_name=MONTHS[m - 1],
                cutoff=2,
                basic=basic_c2,
                deminimis=dm_c2,
                incentive=ZERO,
                thirteenth_month=ZERO,
                gross_cash=c2_gross,
                sss=sss_c2,
                philhealth=phic_c2,
                pagibig=hdmf_c2,
                withholding=wtax_c2,
                net_cash=c2_gross - c2_ded,
            )
        )

        gross_cash = c1_gross + c2_gross
        deductions = c1_ded + c2_ded
        months.append(
            MonthLine(
                month=m,
                month_name=MONTHS[m - 1],
                basic=basic_pay,
                deminimis=dm_pay,
                incentive=incentive_pay,
                thirteenth_month=thirteenth,
                gross_cash=gross_cash,
                deductions=deductions,
                net_cash=gross_cash - deductions,
            )
        )

    annual_gross = sum((c.gross_cash for c in cutoffs), ZERO)
    annual_net = sum((c.net_cash for c in cutoffs), ZERO)

    # Annual cash must equal 12 x signed gross plus the 13th-month payment —
    # the invariant that proves no money was created or lost by re-timing.
    expected_gross = gross_pay * TWELVE + thirteenth_pay
    reconciles = annual_gross == expected_gross

    notes = [
        "Rollout lag: the incentive is paid one month in arrears, so the first "
        "cutoff 1 after go-live carries no incentive. Steady state is shown here.",
    ]
    if b.thirteenth_month_payment > ZERO:
        notes.append(
            "The 13th-month payment falls on December cutoff 1 so it lands on or "
            "before 24 December, as PD 851 requires."
        )
    if not reconciles:
        notes.append(
            f"RECONCILIATION FAILED: annual cash {annual_gross:,.2f} against an "
            f"expected {expected_gross:,.2f}."
        )

    return EmployeeSchedule(
        employee_id=b.employee_id,
        name=b.name,
        months=months,
        cutoffs=cutoffs,
        annual_gross_cash=annual_gross,
        annual_net_cash=annual_net,
        reconciles=reconciles,
        notes=notes,
    )


def build_schedules(
    breakdowns: List[Breakdown], p: Parameters
) -> List[EmployeeSchedule]:
    return [build_schedule(b, p) for b in breakdowns]
