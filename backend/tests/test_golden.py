"""The acceptance criterion for the whole port.

The engine must reproduce COMPUTATIONS.xlsx -> Optimized Structure, rows 44-59,
field for field. If this fails, nothing built on top of the engine can be trusted,
regardless of how the UI looks.

Tolerance is one centavo. Excel computes in binary float and the engine computes in
Decimal, so exact equality is not expected; anything larger than a centavo is a real
disagreement, not float noise.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from app.defaults import default_scenario
from app.engine import compute

GOLDEN = json.loads((Path(__file__).parent / "golden.json").read_text(encoding="utf-8"))
TOLERANCE = Decimal("0.01")

FIELDS = [
    "signed_gross_monthly",
    "deminimis_monthly",
    "thirteenth_month_payment",
    "incentive_monthly",
    "basic_monthly",
    "daily_rate",
    "sss_employee",
    "philhealth_employee",
    "pagibig_employee",
    "net_taxable_monthly",
    "bucket_annual",
    "spill_annual",
    "annual_taxable",
    "annual_tax",
    "withholding_monthly",
    "net_pay_monthly",
    "total_exempt_annual",
    "baseline_basic_monthly",
    "baseline_annual_taxable",
    "baseline_annual_tax",
    "tax_saved_annual",
    "bir_deminimis_annual",
    "bir_benefits_annual",
    "bir_taxable_spill",
]


@pytest.fixture(scope="module")
def result():
    return compute(default_scenario())


@pytest.fixture(scope="module")
def by_id(result):
    return {b.employee_id: b for b in result.breakdowns}


def test_seed_matches_workbook_headcount(result):
    assert len(result.breakdowns) == len(GOLDEN["employees"]) == 16


def test_deminimis_total(result):
    """RR 29-2025 ceilings. Not 6,400.00 — see default_deminimis for the rounding."""
    assert result.deminimis_monthly == Decimal("6399.99")


@pytest.mark.parametrize(
    "expected", GOLDEN["employees"], ids=[e["id"] for e in GOLDEN["employees"]]
)
def test_employee_matches_workbook(by_id, expected):
    got = by_id[expected["id"]]
    assert got.name == expected["name"]
    assert got.restructure == expected["restructure"]

    mismatches = []
    for f in FIELDS:
        if expected[f] is None:
            continue
        want = Decimal(expected[f])
        have = getattr(got, f)
        if abs(have - want) > TOLERANCE:
            mismatches.append(f"{f}: workbook={want} engine={have} delta={have - want}")

    assert not mismatches, "\n".join([f"{expected['name']} (row {expected['row']})"] + mismatches)


def test_total_tax_saved(result):
    want = Decimal(GOLDEN["totals"]["tax_saved_annual"])
    assert abs(result.totals.tax_saved_annual - want) <= TOLERANCE


def test_total_gross_and_basic(result):
    for field in ("signed_gross_monthly", "basic_monthly", "incentive_monthly"):
        want = Decimal(GOLDEN["totals"][field])
        have = getattr(result.totals, field)
        assert abs(have - want) <= TOLERANCE, field


def test_every_restructured_employee_reaches_the_ceiling(by_id):
    """PAYROLL_MODEL.md section 7: exempt = 12D + MIN(bucket, C).

    Under RR 29-2025 that is 76,799.88 + 90,000 = 166,799.88.
    """
    for b in by_id.values():
        if b.restructure and not b.saturated:
            assert b.total_exempt_annual == Decimal("166799.88"), b.name


def test_garcia_is_saturated_and_explained(by_id):
    """Still saturated, but no longer a dead end.

    His 13th-month payment alone overshoots the ceiling, so his bucket spills
    however the incentive is set. Under the old schedule that left him at exactly
    zero saving. The larger RR 29-2025 de minimis comes out of taxable basic
    directly, which the spill does not touch — so he now saves real money.
    """
    garcia = by_id["garcia"]
    assert garcia.saturated
    assert garcia.spill_annual > 0
    assert garcia.tax_saved_annual > Decimal("0")
    assert any("Saturated" in n for n in garcia.notes)
