"""
examples/finance.py
~~~~~~~~~~~~~~~~~~~~
Demonstrates decimallib in financial contexts where exact decimal
arithmetic is mandatory: invoicing, VAT, and compound interest.
"""

from decimallib import DecimalNumber, ROUND_HALF_EVEN
from decimallib import ROUND_HALF_UP, ROUND_TRUNC


def separator(title):
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print('─' * 55)


# ── 1. Invoice with VAT ────────────────────────────────────────

separator("1. Invoice with VAT (20%)")

VAT_RATE  = DecimalNumber('0.20')
ONE       = DecimalNumber('1')
ZERO      = DecimalNumber('0')

items = [
    ("Widget A",  '3',  '12.99'),
    ("Widget B",  '1',  '49.00'),
    ("Widget C",  '12',  '4.50'),
]

print(f"  {'Item':<12} {'Qty':>4} {'Unit':>8} {'Subtotal':>10}")
print(f"  {'─'*12} {'─'*4} {'─'*8} {'─'*10}")

subtotal = ZERO
for name, qty, unit in items:
    q  = DecimalNumber(qty)
    u  = DecimalNumber(unit)
    line = q * u
    line.quantize(2, ROUND_HALF_EVEN)
    subtotal = subtotal + line
    print(f"  {name:<12} {qty:>4} {unit:>8} {line.get():>10}")

vat = subtotal * VAT_RATE
vat.quantize(2, ROUND_HALF_EVEN)
total = subtotal + vat

print(f"\n  {'Subtotal':>26} {subtotal.get():>10}")
print(f"  {'VAT (20%)':>26} {vat.get():>10}")
print(f"  {'─'*36}")
print(f"  {'TOTAL':>26} {total.get():>10}")

# Demonstrate the float error on the same calculation
float_subtotal = sum(int(q) * float(u) for _, q, u in items)
float_vat      = round(float_subtotal * 0.20, 2)
float_total    = float_subtotal + float_vat
print(f"\n  Float result for comparison : {float_total:.10f}")
print(f"  Decimal result              : {total.get()}")


# ── 2. Splitting a bill equally ────────────────────────────────

separator("2. Splitting €100.00 among 3 people")

amount = DecimalNumber('100.00')
n      = DecimalNumber('3')

share_exact = amount.divide(n, scale=10, mode=ROUND_HALF_EVEN)
print(f"  Exact share      : {share_exact.get()}")

# Round each share down (TRUNC), the remainder goes to the last person
share_floor = amount.divide(n, scale=2, mode=ROUND_TRUNC)
remainder   = amount - (share_floor + share_floor + share_floor)

print(f"  Per person (floor) : {share_floor.get()}")
print(f"  Remainder          : {remainder.get()}")
print(f"  Check: 3 × {share_floor.get()} + {remainder.get()} = "
      f"{(DecimalNumber('3') * share_floor + remainder).get()}")


# ── 3. Compound interest ───────────────────────────────────────

separator("3. Compound interest")

principal = DecimalNumber('10000.00')
rate      = DecimalNumber('0.035')   # 3.5% annual
ONE       = DecimalNumber('1')

print(f"  Principal : {principal.get()}")
print(f"  Rate      : 3.5% per year")
print()
print(f"  {'Year':>6}  {'Balance':>14}  {'Interest':>12}")
print(f"  {'─'*6}  {'─'*14}  {'─'*12}")

balance = principal.copy()
for year in range(1, 11):
    interest = balance * rate
    interest.quantize(2, ROUND_HALF_EVEN)
    balance  = balance + interest
    balance.quantize(2, ROUND_HALF_EVEN)
    print(f"  {year:>6}  {balance.get():>14}  {interest.get():>12}")

# Compare with float
float_balance = 10000.0
for _ in range(10):
    float_balance *= 1.035
print(f"\n  Decimal after 10 years : {balance.get()}")
print(f"  Float   after 10 years : {float_balance:.2f}")


# ── 4. Currency conversion with rounding ──────────────────────

separator("4. Currency conversion  EUR → USD → EUR")

eur_usd = DecimalNumber('1.0823')   # exchange rate
usd_eur = DecimalNumber('1').divide(eur_usd, scale=6, mode=ROUND_HALF_EVEN)

amount_eur    = DecimalNumber('1234.56')
amount_usd    = amount_eur * eur_usd
amount_usd.quantize(2, ROUND_HALF_EVEN)
back_to_eur   = amount_usd.divide(eur_usd, scale=2, mode=ROUND_HALF_EVEN)

print(f"  Rate         : 1 EUR = {eur_usd.get()} USD")
print(f"  Amount       : {amount_eur.get()} EUR")
print(f"  Converted    : {amount_usd.get()} USD")
print(f"  Back to EUR  : {back_to_eur.get()} EUR")
print(f"  Rounding loss: {(amount_eur - back_to_eur).get()} EUR  ← explicit, not hidden")
