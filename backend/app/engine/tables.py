"""Statutory lookup tables: TRAIN income tax and SSS contributions.

Both use "largest lower bound <= x", which is what the workbook's MATCH(...,1) does.

SSS data is extracted from COMPUTATIONS.xlsx -> Sheet9, columns A (lower bound) and
L (employee share). Column B of that sheet is NOT used: it carries two known data
errors (B56, B66) documented in PAYROLL_MODEL.md section 3. Column A is clean and
monotonic, so matching on it sidesteps them.
"""

from decimal import Decimal
from typing import List, Tuple

from .money import dec

# --- TRAIN annual income tax, effective 2023 onward ------------------------
# (lower bound, base tax, rate on excess). The workbook keeps a separate
# "threshold" column D, but it is identical to column A in every row, so the
# lower bound doubles as the subtraction base.
TRAIN_BRACKETS: List[Tuple[Decimal, Decimal, Decimal]] = [
    (dec("0"), dec("0"), dec("0")),
    (dec("250000"), dec("0"), dec("0.15")),
    (dec("400000"), dec("22500"), dec("0.20")),
    (dec("800000"), dec("102500"), dec("0.25")),
    (dec("2000000"), dec("402500"), dec("0.30")),
    (dec("8000000"), dec("2202500"), dec("0.35")),
]

# --- SSS 2025 schedule: (MSC lower bound, employee share) ------------------
# 15% total premium, 5% employee. MSC runs 5,000-35,000; the employee share
# tops out at 1,750 and stays there for any compensation above the ceiling.
SSS_BRACKETS: List[Tuple[Decimal, Decimal]] = [
    (dec(str(lower)), dec(str(share)))
    for lower, share in [
        (0, 250), (5250, 275), (5750, 300), (6250, 325), (6750, 350),
        (7250, 375), (7750, 400), (8250, 425), (8750, 450), (9250, 475),
        (9750, 500), (10250, 525), (10750, 550), (11250, 575), (11750, 600),
        (12250, 625), (12750, 650), (13250, 675), (13750, 700), (14250, 725),
        (14750, 750), (15250, 775), (15750, 800), (16250, 825), (16750, 850),
        (17250, 875), (17750, 900), (18250, 925), (18750, 950), (19250, 975),
        (19750, 1000), (20250, 1025), (20750, 1050), (21250, 1075), (21750, 1100),
        (22250, 1125), (22750, 1150), (23250, 1175), (23750, 1200), (24250, 1225),
        (24750, 1250), (25250, 1275), (25750, 1300), (26250, 1325), (26750, 1350),
        (27250, 1375), (27750, 1400), (28250, 1425), (28750, 1450), (29250, 1475),
        (29750, 1500), (30250, 1525), (30750, 1550), (31250, 1575), (31750, 1600),
        (32250, 1625), (32750, 1650), (33250, 1675), (33750, 1700), (34250, 1725),
        (34750, 1750),
    ]
]


def _match_floor(value: Decimal, bounds: List[Decimal]) -> int:
    """Index of the largest bound <= value. Mirrors Excel MATCH(value, range, 1).

    Values below the first bound clamp to index 0, matching the workbook, where the
    first SSS bound is 0 and the first tax bracket is 0 — so this cannot be reached
    with non-negative input.
    """
    lo, hi, found = 0, len(bounds) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if bounds[mid] <= value:
            found, lo = mid, mid + 1
        else:
            hi = mid - 1
    return found


_TRAIN_BOUNDS = [b[0] for b in TRAIN_BRACKETS]
_SSS_BOUNDS = [b[0] for b in SSS_BRACKETS]


def annual_income_tax(taxable: Decimal) -> Decimal:
    """TRAIN annual tax on taxable compensation. Negative input yields zero."""
    if taxable <= 0:
        return dec(0)
    lower, base, rate = TRAIN_BRACKETS[_match_floor(taxable, _TRAIN_BOUNDS)]
    return base + (taxable - lower) * rate


def sss_employee_share(compensation: Decimal) -> Decimal:
    """Employee SSS contribution for a month's compensation.

    The model looks this up on gross less de minimis, not on basic — see
    PAYROLL_MODEL.md section 8. Above the MSC ceiling the share is flat at 1,750.
    """
    if compensation <= 0:
        return SSS_BRACKETS[0][1]
    return SSS_BRACKETS[_match_floor(compensation, _SSS_BOUNDS)][1]
