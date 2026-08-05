"""The model.

Implements PAYROLL_MODEL.md sections 7 and 8. Every formula here has a counterpart
column in COMPUTATIONS.xlsx -> Optimized Structure, noted alongside. Where this file
and that document disagree, the document is right and this file has a bug.

Pure: no I/O, no framework imports, no globals. Same input, same output, always.
"""

from decimal import Decimal
from typing import List

from .models import (
    Breakdown,
    Employee,
    Invariants,
    Parameters,
    Result,
    Scenario,
    Totals,
)
from .money import TWELVE, dec
from .money import clamp
from .tables import annual_income_tax, sss_employee_share

ZERO = dec(0)


def _incentive(
    gross: Decimal,
    deminimis: Decimal,
    thirteenth_payment: Decimal,
    restructure: bool,
    p: Parameters,
) -> Decimal:
    """Column G — the optimizer.

    Non-restructured employees get `cash_anchor - deminimis`, which forces
    `deminimis + incentive = cash_anchor` and therefore pins basic salary to
    `gross - cash_anchor`, exactly the baseline. That is the hold-harmless rule:
    changing the de minimis schedule can never push these employees into tax.

    Restructured employees get the largest incentive satisfying all three
    constraints in PAYROLL_MODEL.md section 7:

        (i)   12A + P <= ceiling     bucket must not exceed 90,000
        (ii)  P >= B                 the 13th-month payment must cover the
                                     statutory 13th month
        (iii) B >= floor             minimum wage

    (ii) binds for high earners, (i) for everyone else, (iii) is a safety stop.
    """
    if not restructure:
        return p.cash_anchor - deminimis

    lower = max(
        gross - deminimis - thirteenth_payment,          # (ii)
        (p.benefits_ceiling - thirteenth_payment) / TWELVE,  # (i)
        ZERO,
    )
    upper = max(ZERO, gross - deminimis - p.minimum_basic_monthly)  # (iii)
    return min(lower, upper)


def compute_employee(
    employee: Employee, deminimis: Decimal, p: Parameters
) -> Breakdown:
    """One employee, start to finish."""
    gross = employee.signed_gross_monthly

    # --- structure ---------------------------------------------------------
    thirteenth_payment = gross - p.cash_anchor                       # F
    incentive = _incentive(
        gross, deminimis, thirteenth_payment, employee.restructure, p
    )                                                                # G
    basic = gross - deminimis - incentive                            # H
    daily_rate = basic * TWELVE / p.working_days                     # I

    # --- statutory deductions ---------------------------------------------
    # SSS is looked up on gross less de minimis, not on basic. PhilHealth is on
    # basic only, correctly excluding de minimis and the incentive.
    sss = sss_employee_share(gross - deminimis)                      # K
    philhealth = (
        clamp(basic, p.philhealth_floor, p.philhealth_ceiling) * p.philhealth_rate
    )                                                                # L
    pagibig = p.pagibig_employee                                     # M
    net_taxable_monthly = basic - sss - philhealth - pagibig         # N

    # --- annual ------------------------------------------------------------
    bucket = incentive * TWELVE + thirteenth_payment                 # O
    spill = max(ZERO, bucket - p.benefits_ceiling)                   # P
    annual_taxable = net_taxable_monthly * TWELVE + spill            # Q
    annual_tax = annual_income_tax(annual_taxable)                   # R
    withholding_monthly = annual_tax / TWELVE                        # S
    net_pay = (
        basic + deminimis + incentive - sss - philhealth - pagibig - withholding_monthly
    )                                                                # T
    total_exempt = deminimis * TWELVE + incentive * TWELVE + thirteenth_payment - spill

    # --- baseline: the pre-optimization structure --------------------------
    # Basic was gross less the cash anchor, with a flat monthly award. SSS and
    # Pag-IBIG are carried across unchanged, matching the workbook.
    base_basic = gross - p.cash_anchor                               # W
    base_philhealth = (
        clamp(base_basic, p.philhealth_floor, p.philhealth_ceiling) * p.philhealth_rate
    )                                                                # X
    base_bucket = base_basic + p.baseline_award * TWELVE             # Y
    base_spill = max(ZERO, base_bucket - p.benefits_ceiling)         # Z
    base_annual_taxable = (
        base_basic - sss - base_philhealth - pagibig
    ) * TWELVE + base_spill                                          # AA
    base_annual_tax = annual_income_tax(base_annual_taxable)         # AB
    tax_saved = base_annual_tax - annual_tax                         # AC

    # --- invariants and explanations ---------------------------------------
    invariants = Invariants(
        structure_balances=(deminimis + incentive + basic == gross),
        minimum_wage_ok=(daily_rate >= p.min_wage_daily),
        thirteenth_month_covered=(thirteenth_payment >= basic),
        held_harmless=None if employee.restructure else (tax_saved == ZERO),
    )

    notes: List[str] = []
    if not employee.restructure:
        notes.append(
            "Not restructured. Held harmless: the incentive is set to "
            "cash anchor minus de minimis, which pins taxable basic to the "
            "baseline, so this employee cannot be pushed into tax by a change "
            "to the de minimis schedule."
        )
    if spill > ZERO:
        notes.append(
            "Saturated. The 13th-month payment alone brings the bucket to "
            f"{bucket:,.2f}, past the {p.benefits_ceiling:,.0f} ceiling, so "
            f"{spill:,.2f} spills into taxable income. Tax saving is limited by "
            "arithmetic, not by an error — the remaining levers are outside this "
            "model (a non-cash achievement award, or an RA 4917 retirement plan)."
        )
    if not invariants.minimum_wage_ok:
        notes.append(
            f"MINIMUM WAGE BREACH. Daily rate {daily_rate:,.2f} is below "
            f"{p.min_wage_daily:,.2f}. This is a wage violation, not a tax outcome."
        )
    if employee.restructure and tax_saved < ZERO:
        notes.append(
            "Restructuring costs this employee money. Check whether the de minimis "
            "schedule changed without the cash anchor being revisited."
        )

    return Breakdown(
        employee_id=employee.id,
        name=employee.name,
        restructure=employee.restructure,
        signed_gross_monthly=gross,
        deminimis_monthly=deminimis,
        thirteenth_month_payment=thirteenth_payment,
        incentive_monthly=incentive,
        basic_monthly=basic,
        daily_rate=daily_rate,
        sss_employee=sss,
        philhealth_employee=philhealth,
        pagibig_employee=pagibig,
        net_taxable_monthly=net_taxable_monthly,
        bucket_annual=bucket,
        spill_annual=spill,
        annual_taxable=annual_taxable,
        annual_tax=annual_tax,
        withholding_monthly=withholding_monthly,
        net_pay_monthly=net_pay,
        total_exempt_annual=total_exempt,
        baseline_basic_monthly=base_basic,
        baseline_annual_taxable=base_annual_taxable,
        baseline_annual_tax=base_annual_tax,
        tax_saved_annual=tax_saved,
        bir_deminimis_annual=deminimis * TWELVE,
        bir_benefits_annual=min(bucket, p.benefits_ceiling),
        bir_taxable_spill=spill,
        invariants=invariants,
        notes=notes,
    )


def compute(scenario: Scenario) -> Result:
    """Every employee, plus totals and scenario-level warnings."""
    p = scenario.parameters
    deminimis = scenario.deminimis_monthly
    breakdowns = [compute_employee(e, deminimis, p) for e in scenario.employees]

    def total(attr: str) -> Decimal:
        return sum((getattr(b, attr) for b in breakdowns), ZERO)

    totals = Totals(
        signed_gross_monthly=total("signed_gross_monthly"),
        deminimis_monthly=total("deminimis_monthly"),
        incentive_monthly=total("incentive_monthly"),
        basic_monthly=total("basic_monthly"),
        net_pay_monthly=total("net_pay_monthly"),
        annual_tax=total("annual_tax"),
        baseline_annual_tax=total("baseline_annual_tax"),
        tax_saved_annual=total("tax_saved_annual"),
        total_exempt_annual=total("total_exempt_annual"),
    )

    warnings: List[str] = []
    for item in scenario.deminimis_items:
        if item.over_cap:
            warnings.append(
                f"{item.label} is granted at {item.granted_monthly:,.2f}/mo against a "
                f"statutory cap of {item.statutory_cap_monthly:,.2f}. The excess does not "
                "stay in Tier 1 — it drops into the 90,000 ceiling and consumes it, while "
                "also reducing basic salary. Cost incurred, no exemption gained."
            )
    breached = [b.name for b in breakdowns if not b.invariants.minimum_wage_ok]
    if breached:
        warnings.append("Minimum wage breach: " + ", ".join(breached))
    unbalanced = [b.name for b in breakdowns if not b.invariants.structure_balances]
    if unbalanced:
        warnings.append(
            "Structure does not balance (de minimis + incentive + basic != gross): "
            + ", ".join(unbalanced)
        )

    return Result(
        deminimis_monthly=deminimis,
        minimum_basic_monthly=p.minimum_basic_monthly,
        breakdowns=breakdowns,
        totals=totals,
        warnings=warnings,
    )
