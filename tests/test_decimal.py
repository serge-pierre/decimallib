"""
tests/test_decimal.py — full test suite for decimallib.

Run with:
    pytest -v
"""

import pytest
from decimallib import (
    DecimalNumber,
    ROUND_TRUNC, ROUND_FLOOR, ROUND_CEIL,
    ROUND_HALF_UP, ROUND_HALF_TOWARD_ZERO, ROUND_HALF_AWAY_ZERO,
    ROUND_HALF_EVEN, ROUND_HALF_PROPORTIONAL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def dn(s):
    """Shorthand: DecimalNumber from string."""
    return DecimalNumber(s)


def q(s, scale, mode):
    """Build a DecimalNumber, quantize it, return get()."""
    n = dn(s)
    n.quantize(scale, mode)
    return n.get()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:

    @pytest.mark.parametrize("s", [
        '', '.', '+', '-', '+.', '-.', 'abc', '1.2.3', '++1',
    ])
    def test_invalid_strings_raise(self, s):
        with pytest.raises(ValueError):
            DecimalNumber(s)

    @pytest.mark.parametrize("s", [None, 42, 3.14, [], {}])
    def test_non_string_raises(self, s):
        with pytest.raises((ValueError, TypeError)):
            DecimalNumber(s)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

class TestNormalisation:

    @pytest.mark.parametrize("s, expected", [
        ('-000.3033', '-0.3033'),
        ('+000.3033', '0.3033'),
        ('123.4500',  '123.45'),
        ('0000',      '0'),
        ('-0',        '0'),
        ('+0',        '0'),
        ('.123',      '0.123'),
        ('123.',      '123'),
        ('000.000',   '0'),
    ])
    def test_normalisation(self, s, expected):
        assert dn(s).get() == expected

    @pytest.mark.parametrize("s, expected_sign", [
        ('0',    0),
        ('-0',   0),
        ('+0',   0),
        ('1',    1),
        ('-1',  -1),
    ])
    def test_zero_sign(self, s, expected_sign):
        assert dn(s).sign == expected_sign


# ---------------------------------------------------------------------------
# Quantize — padding
# ---------------------------------------------------------------------------

class TestQuantizePadding:

    @pytest.mark.parametrize("s, scale, expected", [
        ('123.45', 4, '123.4500'),
        ('123',    3, '123.000'),
        ('0',      2, '0.00'),
    ])
    def test_padding(self, s, scale, expected):
        assert q(s, scale, ROUND_HALF_EVEN) == expected

    def test_padding_does_not_change_intrinsic_scale(self):
        n = dn('1.5')
        n.quantize(4, ROUND_HALF_EVEN)
        assert n.scale == 1          # intrinsic scale unchanged
        assert n.active_scale == 4   # display scale extended


# ---------------------------------------------------------------------------
# Quantize — geometric rounding modes
# ---------------------------------------------------------------------------

class TestQuantizeGeometric:

    @pytest.mark.parametrize("s, scale, mode, expected", [
        ('1.234',  2, ROUND_TRUNC, '1.23'),
        ('1.234',  2, ROUND_FLOOR, '1.23'),
        ('1.234',  2, ROUND_CEIL,  '1.24'),
        ('-1.234', 2, ROUND_TRUNC, '-1.23'),
        ('-1.234', 2, ROUND_FLOOR, '-1.24'),
        ('-1.234', 2, ROUND_CEIL,  '-1.23'),
    ])
    def test_geometric(self, s, scale, mode, expected):
        assert q(s, scale, mode) == expected


# ---------------------------------------------------------------------------
# Quantize — halfway rounding modes
# ---------------------------------------------------------------------------

class TestQuantizeHalfway:

    @pytest.mark.parametrize("s, scale, mode, expected", [
        # positive 0.35
        ('0.35', 1, ROUND_HALF_UP,           '0.4'),
        ('0.35', 1, ROUND_HALF_TOWARD_ZERO,  '0.3'),
        ('0.35', 1, ROUND_HALF_AWAY_ZERO,    '0.4'),
        ('0.35', 1, ROUND_HALF_EVEN,         '0.4'),   # 3 odd → up
        ('0.35', 1, ROUND_HALF_PROPORTIONAL, '0.4'),
        # even digit: 0.25
        ('0.25', 1, ROUND_HALF_EVEN,         '0.2'),   # 2 even → stay
        ('0.25', 1, ROUND_HALF_PROPORTIONAL, '0.2'),
        # negative -0.35
        ('-0.35', 1, ROUND_HALF_UP,           '-0.3'),  # toward +∞
        ('-0.35', 1, ROUND_HALF_TOWARD_ZERO,  '-0.3'),
        ('-0.35', 1, ROUND_HALF_AWAY_ZERO,    '-0.4'),
        ('-0.35', 1, ROUND_HALF_EVEN,         '-0.4'),
        ('-0.35', 1, ROUND_HALF_PROPORTIONAL, '-0.4'),
    ])
    def test_halfway(self, s, scale, mode, expected):
        assert q(s, scale, mode) == expected

    @pytest.mark.parametrize("s, scale, mode, expected", [
        ('9.999',  2, ROUND_HALF_AWAY_ZERO, '10.00'),
        ('9.995',  2, ROUND_HALF_AWAY_ZERO, '10.00'),
        ('-9.999', 2, ROUND_HALF_AWAY_ZERO, '-10.00'),
    ])
    def test_carry_propagation(self, s, scale, mode, expected):
        assert q(s, scale, mode) == expected

    def test_quantize_to_zero(self):
        n = dn('0.001')
        n.quantize(0, ROUND_TRUNC)
        assert n.get() == '0'
        assert n.sign == 0


# ---------------------------------------------------------------------------
# Addition and subtraction
# ---------------------------------------------------------------------------

class TestAddition:

    @pytest.mark.parametrize("sa, sb, expected", [
        ('12.3',  '0.45',  '12.75'),
        ('1',     '2',     '3'),
        ('0.1',   '0.2',   '0.3'),    # the classic float failure
        ('9.9',   '0.1',   '10'),
        ('99.99', '0.01',  '100'),
        ('-1.5',  '-2.5',  '-4'),
    ])
    def test_same_sign(self, sa, sb, expected):
        assert (dn(sa) + dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('5',    '-3',    '2'),
        ('3',    '-5',    '-2'),
        ('1.5',  '-1.5',  '0'),
        ('10.00','-0.01', '9.99'),
        ('-10',  '3',     '-7'),
        ('0.3',  '-0.1',  '0.2'),
    ])
    def test_opposite_signs(self, sa, sb, expected):
        assert (dn(sa) + dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('0',   '5.5',  '5.5'),
        ('5.5', '0',    '5.5'),
        ('0',   '0',    '0'),
        ('-0',  '0',    '0'),
    ])
    def test_with_zero(self, sa, sb, expected):
        assert (dn(sa) + dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('5',   '3',    '2'),
        ('3',   '5',    '-2'),
        ('1.5', '1.5',  '0'),
        ('10',  '0.01', '9.99'),
    ])
    def test_subtraction(self, sa, sb, expected):
        assert (dn(sa) - dn(sb)).get() == expected

    def test_add_returns_new_object(self):
        a = dn('1')
        b = dn('2')
        c = a + b
        assert c.get() == '3'
        assert a.get() == '1'   # a unmodified
        assert b.get() == '2'   # b unmodified


# ---------------------------------------------------------------------------
# Multiplication
# ---------------------------------------------------------------------------

class TestMultiplication:

    @pytest.mark.parametrize("sa, sb, expected", [
        ('2',     '3',     '6'),
        ('1.5',   '2',     '3'),
        ('1.5',   '1.5',   '2.25'),
        ('1.23',  '4.567', '5.61741'),
        ('10',    '10',    '100'),
        ('0.1',   '0.1',   '0.01'),
        ('0.1',   '0.2',   '0.02'),
        ('12.34', '0.01',  '0.1234'),
    ])
    def test_basic(self, sa, sb, expected):
        assert (dn(sa) * dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('3',    '-4',   '-12'),
        ('-3',   '4',    '-12'),
        ('-3',   '-4',   '12'),
        ('-1.5', '-1.5', '2.25'),
        ('1.5',  '-2',   '-3'),
    ])
    def test_signs(self, sa, sb, expected):
        assert (dn(sa) * dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('0',    '999',    '0'),
        ('999',  '0',      '0'),
        ('1',    '123.45', '123.45'),
        ('9.9',  '9.9',    '98.01'),
        ('99',   '99',     '9801'),
    ])
    def test_edge_cases(self, sa, sb, expected):
        assert (dn(sa) * dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, expected", [
        ('999',     '999',     '998001'),
        ('9.99',    '9.99',    '99.8001'),
        ('12345',   '6789',    '83810205'),
        ('0.0001',  '0.0001',  '0.00000001'),
        ('9999',    '9999',    '99980001'),
        ('999.999', '999.999', '999998.000001'),
    ])
    def test_stress(self, sa, sb, expected):
        assert (dn(sa) * dn(sb)).get() == expected

    @pytest.mark.parametrize("sa, sb, scale, mode, expected", [
        ('1.23', '4.567', 2, ROUND_HALF_EVEN, '5.62'),
        ('0.1',  '0.1',   1, ROUND_HALF_EVEN, '0'),
        ('2.5',  '2.5',   1, ROUND_HALF_EVEN, '6.2'),
    ])
    def test_mul_then_quantize(self, sa, sb, scale, mode, expected):
        n = dn(sa) * dn(sb)
        n.quantize(scale, mode)
        assert n.get() == expected


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

class TestDivision:

    @pytest.mark.parametrize("sa, sb, scale, mode, expected", [
        ('1',   '2',   1, ROUND_HALF_EVEN, '0.5'),
        ('1',   '4',   2, ROUND_HALF_EVEN, '0.25'),
        ('1',   '8',   3, ROUND_HALF_EVEN, '0.125'),
        ('3',   '4',   2, ROUND_HALF_EVEN, '0.75'),
        ('22',  '2',   0, ROUND_HALF_EVEN, '11'),
        ('1.5', '0.5', 0, ROUND_HALF_EVEN, '3'),
        ('100', '4',   2, ROUND_HALF_EVEN, '25'),
    ])
    def test_exact(self, sa, sb, scale, mode, expected):
        assert dn(sa).divide(dn(sb), scale, mode).get() == expected

    @pytest.mark.parametrize("sa, sb, scale, mode, expected", [
        ('1',  '3', 4, ROUND_HALF_EVEN, '0.3333'),
        ('2',  '3', 4, ROUND_HALF_EVEN, '0.6667'),
        ('1',  '3', 6, ROUND_HALF_EVEN, '0.333333'),
        ('1',  '7', 6, ROUND_HALF_EVEN, '0.142857'),
        ('1',  '6', 4, ROUND_HALF_EVEN, '0.1667'),
        ('10', '3', 2, ROUND_HALF_EVEN, '3.33'),
        ('22', '7', 5, ROUND_HALF_EVEN, '3.14286'),
    ])
    def test_infinite(self, sa, sb, scale, mode, expected):
        assert dn(sa).divide(dn(sb), scale, mode).get() == expected

    @pytest.mark.parametrize("sa, sb, scale, mode, expected", [
        ('6',  '-2', 0, ROUND_HALF_EVEN, '-3'),
        ('-6', '2',  0, ROUND_HALF_EVEN, '-3'),
        ('-6', '-2', 0, ROUND_HALF_EVEN, '3'),
        ('-1', '3',  4, ROUND_HALF_EVEN, '-0.3333'),
    ])
    def test_signs(self, sa, sb, scale, mode, expected):
        assert dn(sa).divide(dn(sb), scale, mode).get() == expected

    @pytest.mark.parametrize("scale, mode, expected", [
        (1, ROUND_TRUNC,           '0.6'),
        (1, ROUND_FLOOR,           '0.6'),
        (1, ROUND_CEIL,            '0.7'),
        (1, ROUND_HALF_UP,         '0.7'),
        (1, ROUND_HALF_TOWARD_ZERO,'0.7'),
        (1, ROUND_HALF_AWAY_ZERO,  '0.7'),
        (1, ROUND_HALF_EVEN,       '0.7'),
    ])
    def test_all_modes_on_two_thirds(self, scale, mode, expected):
        assert dn('2').divide(dn('3'), scale, mode).get() == expected

    @pytest.mark.parametrize("sa, sb, scale, mode, expected", [
        ('0',   '5', 2, ROUND_HALF_EVEN, '0'),
        ('5',   '1', 2, ROUND_HALF_EVEN, '5'),
        ('5',   '1', 0, ROUND_HALF_EVEN, '5'),
        ('1',   '3', 0, ROUND_HALF_EVEN, '0'),
        ('3',   '3', 4, ROUND_HALF_EVEN, '1'),
    ])
    def test_edge_cases(self, sa, sb, scale, mode, expected):
        assert dn(sa).divide(dn(sb), scale, mode).get() == expected

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            dn('1').divide(dn('0'), 2, ROUND_HALF_EVEN)

    def test_invalid_scale(self):
        with pytest.raises(ValueError):
            dn('1').divide(dn('2'), -1, ROUND_HALF_EVEN)

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            dn('1').divide(dn('2'), 2, 'ROUND_INVALID')


# ---------------------------------------------------------------------------
# Internal invariants
# ---------------------------------------------------------------------------

class TestInvariants:

    @pytest.mark.parametrize("sign, digits, scale, expected_get", [
        (1,  [5],          1, '0.5'),
        (1,  [3,3,3,3],    4, '0.3333'),
        (-1, [5],          1, '-0.5'),
        (1,  [1],          2, '0.01'),
        (1,  [1,2,5],      4, '0.0125'),
    ])
    def test_from_parts_invariant(self, sign, digits, scale, expected_get):
        obj = DecimalNumber._from_parts(sign, digits, scale)
        assert len(obj.digits) >= obj.scale + 1, "invariant violated"
        assert obj.get() == expected_get

    def test_from_parts_empty_digits(self):
        obj = DecimalNumber._from_parts(1, [], 0)
        assert obj.get() == '0'

    @pytest.mark.parametrize("s", [
        '0', '-0', '+0', '000.000',
    ])
    def test_zero_normalisation(self, s):
        n = dn(s)
        assert n.sign == 0
        assert n.digits == [0]
        assert n.scale == 0


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------

class TestComparison:

    @pytest.mark.parametrize("sa, sb", [
        ('1',    '1'),
        ('1.50', '1.5'),
        ('-3',   '-3'),
        ('0',    '-0'),
        ('0',    '0'),
        ('0.10', '0.1'),
    ])
    def test_eq(self, sa, sb):
        assert dn(sa) == dn(sb)

    @pytest.mark.parametrize("sa, sb", [
        ('1',   '2'),
        ('-2',  '-1'),
        ('0.1', '0.2'),
        ('-5',  '0'),
        ('-5',  '5'),
    ])
    def test_lt(self, sa, sb):
        assert dn(sa) < dn(sb)

    @pytest.mark.parametrize("sa, sb", [
        ('2',   '1'),
        ('-1',  '-2'),
        ('0.2', '0.1'),
        ('0',   '-5'),
        ('5',   '-5'),
    ])
    def test_gt(self, sa, sb):
        assert dn(sa) > dn(sb)

    @pytest.mark.parametrize("sa, sb", [
        ('1',   '1'),
        ('1',   '2'),
        ('-3',  '-3'),
        ('-4',  '-3'),
    ])
    def test_le(self, sa, sb):
        assert dn(sa) <= dn(sb)

    @pytest.mark.parametrize("sa, sb", [
        ('1',   '1'),
        ('2',   '1'),
        ('-3',  '-3'),
        ('-3',  '-4'),
    ])
    def test_ge(self, sa, sb):
        assert dn(sa) >= dn(sb)

    def test_not_equal(self):
        assert dn('1') != dn('2')
        assert dn('1') != dn('-1')

    def test_sorting(self):
        numbers = [dn('3'), dn('-1'), dn('0'), dn('1.5'), dn('-2.5')]
        result  = [n.get() for n in sorted(numbers)]
        assert result == ['-2.5', '-1', '0', '1.5', '3']

    def test_min_max(self):
        numbers = [dn('3'), dn('-1'), dn('0'), dn('1.5'), dn('-2.5')]
        assert min(numbers).get() == '-2.5'
        assert max(numbers).get() == '3'

    def test_not_implemented_for_non_decimal(self):
        assert dn('1').__eq__(42) == NotImplemented
        assert dn('1').__lt__(42) == NotImplemented


# ---------------------------------------------------------------------------
# __str__ and __repr__
# ---------------------------------------------------------------------------

class TestStringRepresentations:

    def test_str(self):
        assert str(dn('123.45')) == '123.45'
        assert str(dn('-0'))     == '0'

    def test_repr(self):
        assert repr(dn('123.45')) == "DecimalNumber('123.45')"
        assert repr(dn('-0'))     == "DecimalNumber('0')"

    def test_repr_is_reconstructible(self):
        original = dn('1.23')
        # repr gives DecimalNumber('1.23') — eval it back
        reconstructed = eval(repr(original), {'DecimalNumber': DecimalNumber})
        assert reconstructed == original
