# decimallib

Arbitrary-precision decimal arithmetic in pure Python, free of floating-point rounding errors.

## Motivation

Python's built-in `float` cannot represent most decimal fractions exactly:

```python
>>> 0.1 + 0.2
0.30000000000000004
>>> 1.00 - 0.99
0.010000000000000009
```

`decimallib` represents numbers as a list of base-10 digits with an explicit
scale, performing all arithmetic without ever touching a float.

```python
>>> from decimallib import DecimalNumber
>>> (DecimalNumber('0.1') + DecimalNumber('0.2')).get()
'0.3'
>>> (DecimalNumber('1.00') - DecimalNumber('0.99')).get()
'0.01'
```

## Installation

```bash
# From the project root, inside your virtual environment:
pip install -e .[dev]
```

Requires Python ≥ 3.10.

## Quick start

```python
from decimallib import DecimalNumber, ROUND_HALF_EVEN

a = DecimalNumber('1.23')
b = DecimalNumber('4.567')

# Arithmetic — results are exact at the natural scale
(a + b).get()    # '5.797'
(a - b).get()    # '-3.337'
(a * b).get()    # '5.61741'

# Division — scale and rounding mode are mandatory
a.divide(b, scale=6, mode=ROUND_HALF_EVEN).get()   # '0.269369'

# Quantize — round to a target scale in place
n = a * b
n.quantize(2, ROUND_HALF_EVEN)
n.get()                                             # '5.62'

# Exponentiation
(DecimalNumber('1.5') ** 3).get()                   # '3.375'  (exact)
DecimalNumber('2').power(-3, scale=6, mode=ROUND_HALF_EVEN).get()  # '0.125'

# Comparisons
DecimalNumber('1.5') > DecimalNumber('1.23')        # True
DecimalNumber('1.50') == DecimalNumber('1.5')       # True

# Unary operations
(-DecimalNumber('1.23')).get()                      # '-1.23'
abs(DecimalNumber('-1.23')).get()                   # '1.23'
```

## Examples

The `examples/` directory contains two runnable scripts:

```bash
python examples/float_comparison.py   # float vs decimal side-by-side
python examples/finance.py            # invoice, compound interest, currency
```

`float_comparison.py` demonstrates cases where float arithmetic silently
produces wrong results that decimallib handles exactly.

`finance.py` shows practical financial calculations: VAT invoicing, bill
splitting, 10-year compound interest, and currency conversion with explicit
rounding loss tracking.

## API reference

### `DecimalNumber(string)`

Constructs a decimal number from a string.

**Accepted formats:** `"123"`, `"-45.6"`, `"+.5"`, `"123."`, `".123"`, `"000.000"`  
**Rejected:** `""`, `"."`, `"+"`, `"-"`, `"abc"`, `"1.2.3"`

---

### `.get() → str`

Returns the string representation at `active_scale`.

```python
DecimalNumber('123.4500').get()   # '123.45'
```

---

### `.quantize(new_scale, mode)`

Adjusts `active_scale` in place. Reducing applies rounding permanently;
extending adds virtual trailing zeros (reversible).

---

### `a + b` / `a - b`

Exact. Result scale = `max(a.scale, b.scale)`.

---

### `a * b`

Exact. Result scale = `a.scale + b.scale`.

---

### `a.divide(b, scale, mode) → DecimalNumber`

Divides `a` by `b`, rounded to `scale` places. Scale and mode are mandatory.
Raises `ZeroDivisionError` if `b` is zero.

---

### `a ** n`

Non-negative integer exponents only. Exact result using fast exponentiation.
For negative exponents use `a.power(n, scale, mode)`.

---

### `a.power(n, scale, mode) → DecimalNumber`

Any integer exponent (including negative), rounded to `scale` places.

---

### Comparisons

`==`, `!=`, `<`, `<=`, `>`, `>=` — compatible with `sorted()`, `min()`, `max()`.

---

### Unary operations

`-a`, `abs(a)`, `+a`, `a.copy()`

---

### `str(a)` / `repr(a)`

`repr` is reconstructible: `eval(repr(a)) == a`.

---

### Rounding modes

| Constant | Behaviour | `1.5 →` | `-1.5 →` |
|---|---|---|---|
| `ROUND_TRUNC` | toward zero | `1` | `-1` |
| `ROUND_FLOOR` | toward −∞ | `1` | `-2` |
| `ROUND_CEIL` | toward +∞ | `2` | `-1` |
| `ROUND_HALF_UP` | 0.5 toward +∞ | `2` | `-1` |
| `ROUND_HALF_TOWARD_ZERO` | 0.5 toward zero | `1` | `-1` |
| `ROUND_HALF_AWAY_ZERO` | 0.5 away from zero | `2` | `-2` |
| `ROUND_HALF_EVEN` | 0.5 to nearest even (banker's) | `2` | `-2` |
| `ROUND_HALF_PROPORTIONAL` | 0.5 by digit-sum parity | ~50/50 | |

---

### Internal representation

```
sign         : int        -1, 0, or +1
digits       : list[int]  base-10 digits, most significant first
                          invariant: len(digits) >= scale + 1
scale        : int        number of fractional digits (intrinsic)
active_scale : int        display/computation scale (>= scale)
```

## Running the tests

```bash
pip install -e .[dev]
pytest -v
```

## Project structure

```
decimallib/
├── decimallib/
│   ├── __init__.py      # public API
│   ├── decimal.py       # DecimalNumber class
│   ├── rounding.py      # rounding constants and apply_rounding()
│   └── validators.py    # input validation helpers
├── examples/
│   ├── float_comparison.py
│   └── finance.py
├── tests/
│   └── test_decimal.py  # pytest suite
├── pyproject.toml
├── README.md
└── .gitignore
```

## Git and GitHub

```bash
git init
git add .
git commit -m "Initial commit — decimallib v0.1.0"

# Create an empty repository on GitHub (no README, no .gitignore), then:
git remote add origin github.com/<your-username>/decimallib.git
git branch -M main
git push -u origin main
```
