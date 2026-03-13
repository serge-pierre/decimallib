# decimallib

Arbitrary-precision decimal arithmetic in pure Python, free of floating-point rounding errors.

## Motivation

Python's built-in `float` cannot represent most decimal fractions exactly:

```python
>>> 0.1 + 0.2
0.30000000000000004
```

`decimallib` represents numbers as a list of base-10 digits with an explicit
scale, performing all arithmetic without ever touching a float.

```python
>>> from decimallib import DecimalNumber
>>> (DecimalNumber('0.1') + DecimalNumber('0.2')).get()
'0.3'
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
n = a * b           # '5.61741'
n.quantize(2, ROUND_HALF_EVEN)
n.get()             # '5.62'
```

## API reference

### `DecimalNumber(string)`

Constructs a decimal number from a string.

**Accepted formats:** `"123"`, `"-45.6"`, `"+.5"`, `"123."`, `".123"`, `"000.000"`  
**Rejected:** `""`, `"."`, `"+"`, `"-"`, `"abc"`, `"1.2.3"`

```python
DecimalNumber('123.45')
DecimalNumber('-0.001')
DecimalNumber('+1000')
```

---

### `.get() → str`

Returns the string representation of the number at `active_scale`.

```python
DecimalNumber('123.4500').get()   # '123.45'  (trailing zeros removed)
```

---

### `.quantize(new_scale, mode)`

Adjusts `active_scale` to `new_scale`, in place.

- **Reducing** (`new_scale < active_scale`): applies rounding — permanently
  modifies the stored value.
- **Extending** (`new_scale > active_scale`): adds virtual trailing zeros for
  display only; the stored value is unchanged and reversible.

```python
n = DecimalNumber('1.23456')
n.quantize(2, ROUND_HALF_EVEN)
n.get()   # '1.23'
```

---

### `a + b` / `a - b`

Returns a new `DecimalNumber`. Result scale = `max(a.scale, b.scale)`. Exact.

---

### `a * b`

Returns a new `DecimalNumber`. Result scale = `a.scale + b.scale`. Exact.

---

### `a.divide(b, scale, mode) → DecimalNumber`

Divides `a` by `b`, rounding to `scale` decimal places using `mode`.

Scale and mode are **mandatory** — division can produce infinite decimal
expansions (e.g. `1/3`), so an explicit precision target is required.

```python
DecimalNumber('1').divide(DecimalNumber('3'), scale=4, mode=ROUND_HALF_EVEN).get()
# '0.3333'
```

Raises `ZeroDivisionError` if `b` is zero.

---

### Rounding modes

| Constant | Behaviour | Example: `1.5 →` | Example: `-1.5 →` |
|---|---|---|---|
| `ROUND_TRUNC` | toward zero | `1` | `-1` |
| `ROUND_FLOOR` | toward −∞ | `1` | `-2` |
| `ROUND_CEIL` | toward +∞ | `2` | `-1` |
| `ROUND_HALF_UP` | 0.5 toward +∞ | `2` | `-1` |
| `ROUND_HALF_TOWARD_ZERO` | 0.5 toward zero | `1` | `-1` |
| `ROUND_HALF_AWAY_ZERO` | 0.5 away from zero | `2` | `-2` |
| `ROUND_HALF_EVEN` | 0.5 to nearest even (banker's) | `2` | `-2` |
| `ROUND_HALF_PROPORTIONAL` | 0.5 by digit-sum parity | deterministic ~50/50 | |

---

### Internal representation

```
sign   : int        -1, 0, or +1
digits : list[int]  base-10 digits, most significant first
                    e.g. -123.45 → sign=-1, digits=[1,2,3,4,5], scale=2
scale  : int        number of fractional digits
                    invariant: len(digits) >= scale + 1
active_scale : int  display/computation scale (>= scale)
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
├── tests/
│   └── test_decimal.py  # pytest suite
├── pyproject.toml
├── README.md
└── .gitignore
```

## Git and GitHub

```bash
# Inside the project directory:
git init
git add .
git commit -m "Initial commit — decimallib v0.1.0"

# Create an empty repository on GitHub (no README, no .gitignore),
# then push:
git remote add origin https://github.com/<your-username>/decimallib.git
git branch -M main
git push -u origin main
```
