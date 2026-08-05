"""Decimal helpers.

The whole engine runs on Decimal. No float is constructed anywhere: rates come from
strings, and arithmetic carries full precision through to the end, matching Excel's
behaviour of never rounding intermediates. Quantization happens once, at the API
boundary, via `peso`.
"""

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Union

# 28 digits is the default and is far more than payroll needs, but be explicit:
# a future change to the context should not silently alter results.
getcontext().prec = 28

Number = Union[int, str, Decimal, float]

ZERO = Decimal("0")
TWELVE = Decimal("12")
CENT = Decimal("0.01")


def dec(value: Number) -> Decimal:
    """Coerce to Decimal without ever going through binary float.

    A float argument is routed via `repr` so that 0.025 becomes Decimal("0.025")
    rather than the exact binary expansion. Callers should still pass strings.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(repr(value))
    return Decimal(value)


def peso(value: Number) -> Decimal:
    """Round to centavos, half up. Display only — never feed this back into the model."""
    return dec(value).quantize(CENT, rounding=ROUND_HALF_UP)


def clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    """MIN(MAX(value, low), high) — the PhilHealth floor/ceiling pattern."""
    return min(max(value, low), high)
