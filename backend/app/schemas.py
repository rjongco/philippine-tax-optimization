"""Wire format, and the boundary where Decimal becomes a display number.

Inbound values are coerced to Decimal via strings so nothing enters the engine as
binary float. Outbound values are quantized to centavos exactly once, here — the
engine itself never rounds.
"""

from decimal import Decimal
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .engine.models import (
    Breakdown,
    DeMinimisItem,
    Employee,
    Parameters,
    Result,
    Scenario,
)
from .engine.money import dec, peso
from .engine.schedule import CutoffLine, EmployeeSchedule, MonthLine

Money = Union[int, float, str, Decimal]


def out(value: Decimal) -> float:
    """Decimal -> display number. The only rounding in the system."""
    return float(peso(value))


class _Coercing(BaseModel):
    """Any Money field arriving as a float is routed through repr, never binary."""

    @field_validator("*", mode="before")
    @classmethod
    def _to_decimal(cls, v, info):
        annotation = cls.model_fields[info.field_name].annotation
        if annotation is Decimal and v is not None:
            return dec(v)
        return v


# --- inbound ---------------------------------------------------------------


class ParametersIn(_Coercing):
    philhealth_rate: Decimal = dec("0.025")
    philhealth_floor: Decimal = dec("10000")
    philhealth_ceiling: Decimal = dec("100000")
    pagibig_employee: Decimal = dec("200")
    benefits_ceiling: Decimal = dec("90000")
    cash_anchor: Decimal = dec("5300")
    baseline_award: Decimal = dec("1000")
    min_wage_daily: Decimal = dec("695")
    working_days: Decimal = dec("261")

    def to_engine(self) -> Parameters:
        return Parameters(**self.model_dump())


class DeMinimisItemIn(_Coercing):
    key: str
    label: str
    statutory_cap_monthly: Decimal
    granted_monthly: Decimal
    authority: str = ""
    note: str = ""
    unconditional: bool = True

    def to_engine(self) -> DeMinimisItem:
        return DeMinimisItem(**self.model_dump())


class EmployeeIn(_Coercing):
    id: str
    name: str
    signed_gross_monthly: Decimal
    restructure: bool = True

    def to_engine(self) -> Employee:
        return Employee(**self.model_dump())


class ScenarioIn(BaseModel):
    parameters: ParametersIn
    deminimis_items: List[DeMinimisItemIn]
    employees: List[EmployeeIn]

    def to_engine(self) -> Scenario:
        return Scenario(
            parameters=self.parameters.to_engine(),
            deminimis_items=[i.to_engine() for i in self.deminimis_items],
            employees=[e.to_engine() for e in self.employees],
        )


# --- outbound --------------------------------------------------------------


class ParametersOut(BaseModel):
    philhealth_rate: float
    philhealth_floor: float
    philhealth_ceiling: float
    pagibig_employee: float
    benefits_ceiling: float
    cash_anchor: float
    baseline_award: float
    min_wage_daily: float
    working_days: float
    minimum_basic_monthly: float

    @staticmethod
    def of(p: Parameters) -> "ParametersOut":
        return ParametersOut(
            philhealth_rate=float(p.philhealth_rate),
            philhealth_floor=out(p.philhealth_floor),
            philhealth_ceiling=out(p.philhealth_ceiling),
            pagibig_employee=out(p.pagibig_employee),
            benefits_ceiling=out(p.benefits_ceiling),
            cash_anchor=out(p.cash_anchor),
            baseline_award=out(p.baseline_award),
            min_wage_daily=out(p.min_wage_daily),
            working_days=float(p.working_days),
            minimum_basic_monthly=out(p.minimum_basic_monthly),
        )


class DeMinimisItemOut(BaseModel):
    key: str
    label: str
    statutory_cap_monthly: float
    granted_monthly: float
    annual: float
    authority: str
    note: str
    unconditional: bool
    over_cap: bool

    @staticmethod
    def of(i: DeMinimisItem) -> "DeMinimisItemOut":
        return DeMinimisItemOut(
            key=i.key,
            label=i.label,
            statutory_cap_monthly=out(i.statutory_cap_monthly),
            granted_monthly=out(i.granted_monthly),
            annual=out(i.granted_monthly * dec(12)),
            authority=i.authority,
            note=i.note,
            unconditional=i.unconditional,
            over_cap=i.over_cap,
        )


class EmployeeOut(BaseModel):
    id: str
    name: str
    signed_gross_monthly: float
    restructure: bool

    @staticmethod
    def of(e: Employee) -> "EmployeeOut":
        return EmployeeOut(
            id=e.id,
            name=e.name,
            signed_gross_monthly=out(e.signed_gross_monthly),
            restructure=e.restructure,
        )


class ScenarioOut(BaseModel):
    parameters: ParametersOut
    deminimis_items: List[DeMinimisItemOut]
    employees: List[EmployeeOut]
    deminimis_monthly: float

    @staticmethod
    def of(s: Scenario) -> "ScenarioOut":
        return ScenarioOut(
            parameters=ParametersOut.of(s.parameters),
            deminimis_items=[DeMinimisItemOut.of(i) for i in s.deminimis_items],
            employees=[EmployeeOut.of(e) for e in s.employees],
            deminimis_monthly=out(s.deminimis_monthly),
        )


class InvariantsOut(BaseModel):
    structure_balances: bool
    minimum_wage_ok: bool
    thirteenth_month_covered: bool
    held_harmless: Optional[bool]
    all_ok: bool


class BreakdownOut(BaseModel):
    employee_id: str
    name: str
    restructure: bool
    saturated: bool

    signed_gross_monthly: float
    deminimis_monthly: float
    thirteenth_month_payment: float
    incentive_monthly: float
    basic_monthly: float
    daily_rate: float

    sss_employee: float
    philhealth_employee: float
    pagibig_employee: float
    net_taxable_monthly: float

    bucket_annual: float
    spill_annual: float
    annual_taxable: float
    annual_tax: float
    withholding_monthly: float
    net_pay_monthly: float
    total_exempt_annual: float

    baseline_basic_monthly: float
    baseline_annual_taxable: float
    baseline_annual_tax: float
    tax_saved_annual: float

    bir_deminimis_annual: float
    bir_benefits_annual: float
    bir_taxable_spill: float

    invariants: InvariantsOut
    notes: List[str]

    @staticmethod
    def of(b: Breakdown) -> "BreakdownOut":
        money_fields = {
            f: out(getattr(b, f))
            for f in (
                "signed_gross_monthly", "deminimis_monthly",
                "thirteenth_month_payment", "incentive_monthly", "basic_monthly",
                "daily_rate", "sss_employee", "philhealth_employee",
                "pagibig_employee", "net_taxable_monthly", "bucket_annual",
                "spill_annual", "annual_taxable", "annual_tax",
                "withholding_monthly", "net_pay_monthly", "total_exempt_annual",
                "baseline_basic_monthly", "baseline_annual_taxable",
                "baseline_annual_tax", "tax_saved_annual", "bir_deminimis_annual",
                "bir_benefits_annual", "bir_taxable_spill",
            )
        }
        return BreakdownOut(
            employee_id=b.employee_id,
            name=b.name,
            restructure=b.restructure,
            saturated=b.saturated,
            invariants=InvariantsOut(
                structure_balances=b.invariants.structure_balances,
                minimum_wage_ok=b.invariants.minimum_wage_ok,
                thirteenth_month_covered=b.invariants.thirteenth_month_covered,
                held_harmless=b.invariants.held_harmless,
                all_ok=b.invariants.all_ok,
            ),
            notes=b.notes,
            **money_fields,
        )


class TotalsOut(BaseModel):
    signed_gross_monthly: float
    deminimis_monthly: float
    incentive_monthly: float
    basic_monthly: float
    net_pay_monthly: float
    annual_tax: float
    baseline_annual_tax: float
    tax_saved_annual: float
    total_exempt_annual: float


class ResultOut(BaseModel):
    deminimis_monthly: float
    minimum_basic_monthly: float
    breakdowns: List[BreakdownOut]
    totals: TotalsOut
    warnings: List[str]

    @staticmethod
    def of(r: Result) -> "ResultOut":
        t = r.totals
        return ResultOut(
            deminimis_monthly=out(r.deminimis_monthly),
            minimum_basic_monthly=out(r.minimum_basic_monthly),
            breakdowns=[BreakdownOut.of(b) for b in r.breakdowns],
            totals=TotalsOut(
                **{
                    f: out(getattr(t, f))
                    for f in (
                        "signed_gross_monthly", "deminimis_monthly",
                        "incentive_monthly", "basic_monthly", "net_pay_monthly",
                        "annual_tax", "baseline_annual_tax", "tax_saved_annual",
                        "total_exempt_annual",
                    )
                }
            ),
            warnings=r.warnings,
        )


class CutoffOut(BaseModel):
    month: int
    month_name: str
    cutoff: int
    basic: float
    deminimis: float
    incentive: float
    thirteenth_month: float
    gross_cash: float
    sss: float
    philhealth: float
    pagibig: float
    withholding: float
    net_cash: float
    note: str

    @staticmethod
    def of(c: CutoffLine) -> "CutoffOut":
        return CutoffOut(
            month=c.month, month_name=c.month_name, cutoff=c.cutoff, note=c.note,
            **{
                f: out(getattr(c, f))
                for f in (
                    "basic", "deminimis", "incentive", "thirteenth_month",
                    "gross_cash", "sss", "philhealth", "pagibig", "withholding",
                    "net_cash",
                )
            },
        )


class MonthOut(BaseModel):
    month: int
    month_name: str
    basic: float
    deminimis: float
    incentive: float
    thirteenth_month: float
    gross_cash: float
    deductions: float
    net_cash: float

    @staticmethod
    def of(m: MonthLine) -> "MonthOut":
        return MonthOut(
            month=m.month, month_name=m.month_name,
            **{
                f: out(getattr(m, f))
                for f in (
                    "basic", "deminimis", "incentive", "thirteenth_month",
                    "gross_cash", "deductions", "net_cash",
                )
            },
        )


class ScheduleOut(BaseModel):
    employee_id: str
    name: str
    months: List[MonthOut]
    cutoffs: List[CutoffOut]
    annual_gross_cash: float
    annual_net_cash: float
    reconciles: bool
    notes: List[str]

    @staticmethod
    def of(s: EmployeeSchedule) -> "ScheduleOut":
        return ScheduleOut(
            employee_id=s.employee_id,
            name=s.name,
            months=[MonthOut.of(m) for m in s.months],
            cutoffs=[CutoffOut.of(c) for c in s.cutoffs],
            annual_gross_cash=out(s.annual_gross_cash),
            annual_net_cash=out(s.annual_net_cash),
            reconciles=s.reconciles,
            notes=s.notes,
        )
