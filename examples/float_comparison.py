"""
examples/float_comparison.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Illustrates why floating-point arithmetic is unsuitable for exact decimal
calculations, and how decimallib solves the problem.
"""

from decimallib import DecimalNumber, ROUND_HALF_EVEN


def separator(title):
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print('─' * 55)


# ── 1. The classic accumulation error ─────────────────────────

separator("1. Classic accumulation error")

float_sum = 0.0
decimal_sum = DecimalNumber('0')
step = DecimalNumber('0.1')

for _ in range(10):
    float_sum   += 0.1
    decimal_sum  = decimal_sum + step

print(f"  0.1 × 10  —  float   : {float_sum}")
print(f"  0.1 × 10  —  decimal : {decimal_sum.get()}")
print(f"  float == 1.0 ? {float_sum == 1.0}   ← unexpected")
print(f"  decimal == 1 ? {decimal_sum == DecimalNumber('1')}    ← correct")


# ── 2. Simple addition ─────────────────────────────────────────

separator("2. Simple addition  0.1 + 0.2")

print(f"  float   : {0.1 + 0.2}")
print(f"  decimal : {(DecimalNumber('0.1') + DecimalNumber('0.2')).get()}")


# ── 3. Subtraction cancellation ────────────────────────────────

separator("3. Subtraction  1.00 - 0.99")

print(f"  float   : {1.00 - 0.99}")
print(f"  decimal : {(DecimalNumber('1.00') - DecimalNumber('0.99')).get()}")


# ── 4. Multiplication ──────────────────────────────────────────

separator("4. Multiplication  1.23 × 4.567")

print(f"  float   : {1.23 * 4.567}")
print(f"  decimal : {(DecimalNumber('1.23') * DecimalNumber('4.567')).get()}")


# ── 5. Division  1/3  ──────────────────────────────────────────

separator("5. Division  1 ÷ 3  (controlled precision)")

result = DecimalNumber('1').divide(DecimalNumber('3'), scale=20, mode=ROUND_HALF_EVEN)
print(f"  float   : {1/3}")
print(f"  decimal : {result.get()}")
print(f"  (exact to 20 decimal places, rounding mode explicit)")


# ── 6. Rounding half ───────────────────────────────────────────

separator("6. Rounding  2.5 and 3.5 to nearest integer")

print("  Python's built-in round() uses banker's rounding:")
for v in [0.5, 1.5, 2.5, 3.5, 4.5]:
    print(f"    round({v}) = {round(v)}")

print()
print("  decimallib — explicit rounding modes:")
from decimallib import ROUND_HALF_AWAY_ZERO, ROUND_HALF_EVEN
for s in ['0.5', '1.5', '2.5', '3.5', '4.5']:
    n_away = DecimalNumber(s)
    n_even = DecimalNumber(s)
    n_away.quantize(0, ROUND_HALF_AWAY_ZERO)
    n_even.quantize(0, ROUND_HALF_EVEN)
    print(f"    {s}  HALF_AWAY_ZERO={n_away.get()}   HALF_EVEN={n_even.get()}")


# ── 7. Large exact integer multiplication ──────────────────────

separator("7. Large exact multiplication  999999 × 999999")

a = 999999
b = 999999
print(f"  float   : {float(a) * float(b):.1f}  (may lose precision for very large numbers)")
print(f"  decimal : {(DecimalNumber(str(a)) * DecimalNumber(str(b))).get()}")
