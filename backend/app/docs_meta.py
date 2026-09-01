"""Documentation for every configurable value.

This drives the configuration page. The user asked for comprehensive detail on what
each value does, so each entry carries not just a label but its legal authority, what
it affects downstream, and what breaks if it is wrong.

Categories, following PAYROLL_MODEL.md section 6:

  fact        set by law or regulation. Editable, but changing it means the law
              changed — not that you are tuning the model.
  lever       a genuine modelling choice. Meant to be adjusted.
  assumption  a placeholder that has not been verified against a primary source.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel

Category = Literal["fact", "lever", "assumption"]


class ParameterDoc(BaseModel):
    key: str
    label: str
    category: Category
    unit: str
    authority: str
    description: str
    affects: str
    warning: Optional[str] = None
    editable: bool = True


PARAMETER_DOCS: List[ParameterDoc] = [
    ParameterDoc(
        key="philhealth_rate",
        label="PhilHealth employee rate",
        category="fact",
        unit="rate",
        authority="Universal Health Care Act — 5% premium, shared equally",
        description=(
            "The employee's half of the PhilHealth premium. The total premium is 5% "
            "of the salary base; employer and employee split it evenly, so the "
            "employee pays 2.5%."
        ),
        affects=(
            "PhilHealth deduction, which reduces monthly taxable income and therefore "
            "annual tax. A larger deduction slightly increases the tax saving but "
            "reduces take-home pay."
        ),
        warning="Change this only when the statutory premium rate changes.",
    ),
    ParameterDoc(
        key="philhealth_floor",
        label="PhilHealth salary floor",
        category="fact",
        unit="PHP/month",
        authority="PhilHealth premium schedule",
        description=(
            "The minimum salary base for the premium. An employee earning less than "
            "this still contributes as though they earned this."
        ),
        affects="PhilHealth deduction for low earners only.",
    ),
    ParameterDoc(
        key="philhealth_ceiling",
        label="PhilHealth salary ceiling",
        category="fact",
        unit="PHP/month",
        authority="PhilHealth premium schedule",
        description=(
            "The maximum salary base. Earnings above this do not increase the premium."
        ),
        affects=(
            "PhilHealth deduction for high earners. Garcia is the only employee near "
            "this ceiling."
        ),
    ),
    ParameterDoc(
        key="pagibig_employee",
        label="Pag-IBIG employee share",
        category="fact",
        unit="PHP/month",
        authority="HDMF — 2% of the PHP 10,000 fund salary ceiling",
        description=(
            "A flat monthly contribution. The 2% rate applies to a fund salary capped "
            "at PHP 10,000, so almost every employee pays exactly PHP 200."
        ),
        affects="A flat reduction in monthly taxable income for every employee.",
    ),
    ParameterDoc(
        key="benefits_ceiling",
        label="Benefits exclusion ceiling",
        category="fact",
        unit="PHP/year",
        authority="NIRC Sec. 32(B)(7)(e)",
        description=(
            "The combined annual cap on 13th month pay AND other benefits. This is "
            "the ceiling the whole model is built around. It is a single shared "
            "bucket: the 13th-month payment goes in first, and the productivity "
            "incentive fills whatever room is left. Anything beyond it is taxable."
        ),
        affects=(
            "Directly sets the productivity incentive for every restructured "
            "employee. Raising it raises the incentive and the tax saving; lowering "
            "it pushes money into taxable basic salary."
        ),
        warning=(
            "This is the single most important number in the model. It is fixed by "
            "statute at PHP 90,000 and has been since TRAIN. Do not change it to "
            "model a 'what if' — clone the scenario instead."
        ),
    ),
    ParameterDoc(
        key="cash_anchor",
        label="Cash anchor (carve-out per month)",
        category="lever",
        unit="PHP/month",
        authority="Modelling choice, not statutory",
        description=(
            "Sets the 13th-month-date payment as signed gross minus this amount, "
            "which is what fixes each employee's total annual cash. It also defines "
            "hold-harmless: employees who are not restructured receive an incentive "
            "of exactly this amount minus de minimis, which pins their taxable basic "
            "to the old structure."
        ),
        affects=(
            "Total annual cash for every employee, the size of the 13th-month "
            "payment, how much room is left in the 90,000 bucket, and the "
            "hold-harmless guarantee for non-restructured staff."
        ),
        warning=(
            "The most consequential editable cell in the model. Changing it changes "
            "what every employee is actually paid over a year, not just how their pay "
            "is labelled. It is currently set to preserve the prior structure's cash "
            "exactly."
        ),
    ),
    ParameterDoc(
        key="baseline_award",
        label="Baseline award (comparison only)",
        category="lever",
        unit="PHP/month",
        authority="Modelling choice — describes the OLD structure",
        description=(
            "The monthly benefit under the pre-optimization structure. It exists so "
            "the model can show what tax would have been paid before restructuring."
        ),
        affects=(
            "The 'before' comparison and therefore the reported tax saving. It does "
            "NOT affect anyone's actual pay."
        ),
        warning=(
            "This was formerly wired into the live calculation for non-restructured "
            "employees, which silently pushed them into tax whenever the de minimis "
            "schedule changed. It now drives the comparison only. Do not reconnect it "
            "to the incentive."
        ),
    ),
    ParameterDoc(
        key="min_wage_daily",
        label="Minimum wage — daily",
        category="assumption",
        unit="PHP/day",
        authority="Regional wage order — NOT YET VERIFIED",
        description=(
            "The applicable daily minimum wage. The model uses it as a hard floor: "
            "the optimizer will not reduce anyone's basic salary below the monthly "
            "equivalent, no matter how much tax that would save."
        ),
        affects=(
            "The minimum basic salary floor, and the OK / BREACH check on every "
            "employee. A BREACH is a wage violation, not a tax outcome."
        ),
        warning=(
            "PLACEHOLDER. Verify against the wage order actually in force for your "
            "region and industry before relying on the floor check."
        ),
    ),
    ParameterDoc(
        key="working_days",
        label="Working days divisor",
        category="assumption",
        unit="days/year",
        authority="Company policy — NOT YET VERIFIED",
        description=(
            "Days used to convert monthly basic salary into a daily rate. 261 assumes "
            "a five-day week; use 313 for a six-day week."
        ),
        affects="The daily rate, and therefore the minimum wage check.",
        warning=(
            "PLACEHOLDER. Must match the divisor actually used in your payroll. A "
            "wrong divisor makes the minimum wage check meaningless in both "
            "directions."
        ),
    ),
]

DOCS_BY_KEY = {d.key: d for d in PARAMETER_DOCS}


class ConceptDoc(BaseModel):
    key: str
    title: str
    body: str


CONCEPT_DOCS: List[ConceptDoc] = [
    ConceptDoc(
        key="two_tiers",
        title="The two exemption tiers",
        body=(
            "Tier 1 is de minimis (RR 5-2011 as amended). Each item has its own peso "
            "cap, and none of it consumes the PHP 90,000 ceiling — it is free space. "
            "Tier 2 is 13th month pay and other benefits under NIRC Sec. 32(B)(7)(e), "
            "capped at PHP 90,000 a year combined.\n\n"
            "Fill Tier 1 to its caps first, because it costs nothing from Tier 2. "
            "Granting de minimis ABOVE a cap is strictly worse than not granting it: "
            "the excess does not stay in Tier 1, it drops into the 90,000 ceiling and "
            "consumes it, while also reducing basic salary. Cost incurred, no "
            "exemption gained."
        ),
    ),
    ConceptDoc(
        key="ceiling",
        title="Why every restructured employee lands on PHP 166,799.88",
        body=(
            "Exempt income is twelve months of de minimis plus whatever fits in the "
            "90,000 bucket: 12 x 6,399.99 + 90,000 = 166,799.88. That is the mathematical "
            "maximum under Philippine law without paying additional money. It holds "
            "whether the bucket lands exactly on the ceiling or overshoots — an "
            "overshoot just becomes taxable spill."
        ),
    ),
    ConceptDoc(
        key="hold_harmless",
        title="Hold-harmless for employees who are not restructured",
        body=(
            "An employee already below the PHP 250,000 zero bracket gains nothing "
            "from restructuring, while losing 13th month base, SSS accrual and "
            "minimum-wage headroom. Those employees are marked as not restructured.\n\n"
            "They receive an incentive of cash anchor minus de minimis, which forces "
            "de minimis + incentive to equal the cash anchor and therefore pins their "
            "taxable basic to exactly the old structure. This is what makes the "
            "guarantee structural rather than coincidental: changing the de minimis "
            "schedule can no longer push them into tax."
        ),
    ),
    ConceptDoc(
        key="determination",
        title="The productivity incentive needs a real determination",
        body=(
            "Sec. 32(B)(7)(e) covers '13th month pay and other benefits'. A fixed "
            "amount paid unconditionally every month is regular compensation "
            "regardless of what the column is called.\n\n"
            "For the incentive to hold, it needs a threshold that could genuinely "
            "fail and a monthly determination recorded per employee — criteria met, "
            "amount released, approver. Sizing it off gross salary is fine; the 13th "
            "month is one month of basic and nobody disputes its character. "
            "Invariance is the defect, not derivation.\n\n"
            "The app computes the amount. It does not evidence the determination — "
            "that has to happen in your payroll process."
        ),
    ),
]
