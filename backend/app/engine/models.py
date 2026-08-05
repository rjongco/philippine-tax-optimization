"""Engine domain types.

Plain dataclasses on purpose: the engine must be importable and testable without
FastAPI, Pydantic, or a running server. The API layer converts to and from these.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from .money import TWELVE, dec


@dataclass(frozen=True)
class Parameters:
    """Model levers and statutory constants. See PAYROLL_MODEL.md section 6."""

    philhealth_rate: Decimal = dec("0.025")
    philhealth_floor: Decimal = dec("10000")
    philhealth_ceiling: Decimal = dec("100000")
    pagibig_employee: Decimal = dec("200")
    benefits_ceiling: Decimal = dec("90000")
    cash_anchor: Decimal = dec("5300")
    baseline_award: Decimal = dec("1000")
    min_wage_daily: Decimal = dec("695")
    working_days: Decimal = dec("261")

    @property
    def minimum_basic_monthly(self) -> Decimal:
        """The minimum-wage floor the optimizer must not push basic salary below."""
        return self.min_wage_daily * self.working_days / TWELVE


@dataclass(frozen=True)
class DeMinimisItem:
    """One line of the Tier 1 schedule."""

    key: str
    label: str
    statutory_cap_monthly: Decimal
    granted_monthly: Decimal
    authority: str = ""
    note: str = ""
    # False for items whose exemption depends on something the app cannot verify
    # (substantiation on file, payment falling on the right occasion).
    unconditional: bool = True

    @property
    def over_cap(self) -> bool:
        return self.granted_monthly > self.statutory_cap_monthly


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    signed_gross_monthly: Decimal
    restructure: bool = True


@dataclass(frozen=True)
class Scenario:
    parameters: Parameters
    deminimis_items: List[DeMinimisItem]
    employees: List[Employee]

    @property
    def deminimis_monthly(self) -> Decimal:
        return sum((i.granted_monthly for i in self.deminimis_items), dec(0))


@dataclass(frozen=True)
class Invariants:
    """The hard invariants from PAYROLL_MODEL.md section 10, per employee."""

    structure_balances: bool          # D + A + B = G
    minimum_wage_ok: bool             # daily rate >= min wage
    thirteenth_month_covered: bool    # P >= B
    held_harmless: Optional[bool]     # non-restructured employees must not lose (AC >= 0)

    @property
    def all_ok(self) -> bool:
        return (
            self.structure_balances
            and self.minimum_wage_ok
            and self.thirteenth_month_covered
            and self.held_harmless is not False
        )


@dataclass(frozen=True)
class Breakdown:
    """Per-employee result. Workbook column letters noted for traceability."""

    employee_id: str
    name: str
    restructure: bool

    signed_gross_monthly: Decimal        # D
    deminimis_monthly: Decimal           # E
    thirteenth_month_payment: Decimal    # F  (paid on the 13th-month date)
    incentive_monthly: Decimal           # G
    basic_monthly: Decimal               # H
    daily_rate: Decimal                  # I

    sss_employee: Decimal                # K
    philhealth_employee: Decimal         # L
    pagibig_employee: Decimal            # M
    net_taxable_monthly: Decimal         # N

    bucket_annual: Decimal               # O  (12A + P)
    spill_annual: Decimal                # P
    annual_taxable: Decimal              # Q
    annual_tax: Decimal                  # R
    withholding_monthly: Decimal         # S
    net_pay_monthly: Decimal             # T
    total_exempt_annual: Decimal         # U

    baseline_basic_monthly: Decimal      # W
    baseline_annual_taxable: Decimal     # AA
    baseline_annual_tax: Decimal         # AB
    tax_saved_annual: Decimal            # AC

    bir_deminimis_annual: Decimal        # AE
    bir_benefits_annual: Decimal         # AF
    bir_taxable_spill: Decimal           # AG

    invariants: Invariants
    notes: List[str] = field(default_factory=list)

    @property
    def saturated(self) -> bool:
        """True when the 90k bucket is full before any incentive is added."""
        return self.spill_annual > 0


@dataclass(frozen=True)
class Totals:
    signed_gross_monthly: Decimal
    deminimis_monthly: Decimal
    incentive_monthly: Decimal
    basic_monthly: Decimal
    net_pay_monthly: Decimal
    annual_tax: Decimal
    baseline_annual_tax: Decimal
    tax_saved_annual: Decimal
    total_exempt_annual: Decimal


@dataclass(frozen=True)
class Result:
    deminimis_monthly: Decimal
    minimum_basic_monthly: Decimal
    breakdowns: List[Breakdown]
    totals: Totals
    warnings: List[str] = field(default_factory=list)
