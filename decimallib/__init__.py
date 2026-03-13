"""
decimallib — arbitrary-precision decimal arithmetic, free of floating-point rounding.

Public API
----------
    from decimallib import DecimalNumber
    from decimallib import (
        ROUND_TRUNC, ROUND_FLOOR, ROUND_CEIL,
        ROUND_HALF_UP, ROUND_HALF_TOWARD_ZERO, ROUND_HALF_AWAY_ZERO,
        ROUND_HALF_EVEN, ROUND_HALF_PROPORTIONAL,
    )

Basic usage
-----------
    a = DecimalNumber('1.23')
    b = DecimalNumber('4.567')

    (a + b).get()                              # '5.797'
    (a * b).get()                              # '5.61741'
    a.divide(b, scale=4, mode=ROUND_HALF_EVEN) # DecimalNumber('0.2694')

    n = a * b
    n.quantize(2, ROUND_HALF_EVEN)
    n.get()                                    # '5.62'
"""

from .decimal import DecimalNumber
from .rounding import (
    ROUND_TRUNC,
    ROUND_FLOOR,
    ROUND_CEIL,
    ROUND_HALF_UP,
    ROUND_HALF_TOWARD_ZERO,
    ROUND_HALF_AWAY_ZERO,
    ROUND_HALF_EVEN,
    ROUND_HALF_PROPORTIONAL,
)

__all__ = [
    'DecimalNumber',
    'ROUND_TRUNC',
    'ROUND_FLOOR',
    'ROUND_CEIL',
    'ROUND_HALF_UP',
    'ROUND_HALF_TOWARD_ZERO',
    'ROUND_HALF_AWAY_ZERO',
    'ROUND_HALF_EVEN',
    'ROUND_HALF_PROPORTIONAL',
]
