from .validators import is_number_valid, get_scale
from .rounding import (
    _ALL_MODES, apply_rounding,
    ROUND_TRUNC, ROUND_FLOOR, ROUND_CEIL,
    ROUND_HALF_UP, ROUND_HALF_TOWARD_ZERO, ROUND_HALF_AWAY_ZERO,
    ROUND_HALF_EVEN, ROUND_HALF_PROPORTIONAL,
)

class DecimalNumber:
    """
    Arbitrary-precision decimal number, free of floating-point rounding.

    Internal representation
    -----------------------
    sign   : int        -1 (negative), 0 (zero), or 1 (positive)
    digits : list[int]  base-10 digits, most significant first.
                        e.g. 123.45 → [1, 2, 3, 4, 5]
                        Invariant: no leading zeros (except the number zero itself,
                        stored as [0]), no trailing zeros in the fractional part.
    scale  : int        number of digits belonging to the fractional part.
                        e.g. 123.45 → scale=2, 123 → scale=0
                        Invariant: always reflects the digits list exactly.
                        Invariant: len(digits) >= scale + 1  (the integer part
                        always has at least one digit, even for numbers < 1,
                        e.g. 0.5 → digits=[0,5] not [5]).

    Scale management
    ----------------
    active_scale : int  display and computation scale, >= scale.
                        Starts equal to scale at construction.

    quantize(new_scale, mode) has an intentional asymmetry:
      - Reducing  (new_scale < active_scale): rounding is applied; both
        scale and active_scale are updated to new_scale. The stored value
        is permanently modified — quantize() is not merely a display hint.
      - Extending (new_scale > active_scale): only active_scale is updated;
        the trailing zeros are virtual and rendered by get(). No data is lost
        and the operation is reversible by calling quantize(scale, ...).
    """

    def __init__(self, string):
        if not is_number_valid(string):
            raise ValueError(f"Format invalide: {string}")

        # Determine the sign
        if string[0] == '-':
            self.sign = -1
            string = string[1:]
        elif string[0] == '+':
            self.sign = 1
            string = string[1:]
        else:
            self.sign = 1

        # Normalize: .123 -> 0.123  and  123. -> 123
        if string.startswith('.'):
            string = '0' + string
        if string.endswith('.'):
            string = string[:-1]

        self.scale = get_scale(string)

        # Extract the digits
        self.digits = []
        for letter in string:
            if letter == '.':
                continue
            self.digits.append(int(letter))

        # Removal of unnecessary zeros
        self._remove_leading_zeros()
        self._remove_trailing_zeros()

        # Normalize zero: sign is always 0 for any representation of zero
        if all(d == 0 for d in self.digits):
            self.digits = [0]
            self.scale = 0
            self.sign = 0

        # active_scale starts equal to intrinsic scale
        self.active_scale = self.scale

    def _remove_leading_zeros(self):
        """Removes insignificant leading zeros."""
        while len(self.digits) > self.scale + 1 and self.digits[0] == 0:
            self.digits.pop(0)

    def _remove_trailing_zeros(self):
        """Removes insignificant zeros at the end (decimal part)."""
        while self.scale > 0 and self.digits[-1] == 0:
            self.digits.pop()
            self.scale -= 1

    def quantize(self, new_scale, mode):
        """
        Adjusts active_scale to new_scale, in place.

        - new_scale > active_scale : padding (adds trailing zeros, no rounding)
        - new_scale < active_scale : rounding with the given mode
        - new_scale == active_scale: no-op

        Args:
            new_scale (int) : target scale, must be >= 0
            mode      (str) : one of the ROUND_* constants from rounding.py

        Raises:
            ValueError: if new_scale is negative or mode is unknown
        """
        if not isinstance(new_scale, int) or new_scale < 0:
            raise ValueError(f"new_scale doit être un entier >= 0, reçu : {new_scale}")
        if mode not in _ALL_MODES:
            raise ValueError(f"Mode d'arrondi inconnu : {mode}")

        if new_scale == self.active_scale:
            return

        if new_scale > self.active_scale:
            # Padding: get() will render the extra zeros
            self.active_scale = new_scale
            return

        # Rounding: new_scale < active_scale
        # Build padded digit list at active_scale (may include virtual trailing zeros)
        padded_digits = self.digits + [0] * (self.active_scale - self.scale)

        new_digits = apply_rounding(
            padded_digits, self.active_scale, new_scale, self.sign, mode
        )

        self.digits = new_digits
        self.active_scale = new_scale
        self.scale = new_scale

        self._remove_leading_zeros()
        if all(d == 0 for d in self.digits):
            self.digits = [0]
            self.active_scale = 0
            self.scale = 0
            self.sign = 0

    @classmethod
    def _from_parts(cls, sign, digits, scale):
        """
        Internal constructor: builds a DecimalNumber directly from components,
        bypassing string parsing. Normalizes the result (leading/trailing zeros,
        zero sign) and enforces the class invariant len(digits) >= scale + 1.

        Args:
            sign   (int)       : -1, 0, or 1
            digits (list[int]) : base-10 digits, most significant first
            scale  (int)       : number of fractional digits

        Returns:
            DecimalNumber
        """
        obj = object.__new__(cls)
        obj.sign   = sign
        obj.digits = list(digits) if digits else [0]  # guard: never empty
        obj.scale  = scale

        # Invariant: len(digits) >= scale + 1
        # A number like 0.5 needs digits=[0,5], not [5].
        # Without the leading zero, get() would place the decimal point
        # before all digits, producing ".5" instead of "0.5".
        shortage = (obj.scale + 1) - len(obj.digits)
        if shortage > 0:
            obj.digits = [0] * shortage + obj.digits

        obj._remove_leading_zeros()
        obj._remove_trailing_zeros()

        if all(d == 0 for d in obj.digits):
            obj.digits = [0]
            obj.scale  = 0
            obj.sign   = 0

        obj.active_scale = obj.scale
        return obj

    def _compare_abs(self, other):
        """
        Compares the absolute values of self and other.

        Returns:
             1  if |self| > |other|
             0  if |self| == |other|
            -1  if |self| < |other|
        """
        # Align both numbers to the same scale for digit-by-digit comparison
        common_scale = max(self.scale, other.scale)
        a = self.digits  + [0] * (common_scale - self.scale)
        b = other.digits + [0] * (common_scale - other.scale)

        # Pad the shorter integer part with leading zeros
        a_int = len(a) - common_scale
        b_int = len(b) - common_scale
        max_int = max(a_int, b_int)
        a = [0] * (max_int - a_int) + a
        b = [0] * (max_int - b_int) + b

        # Compare digit by digit, most significant first
        for da, db in zip(a, b):
            if da > db: return  1
            if da < db: return -1
        return 0

    def _align(self, other):
        """
        Returns two digit lists padded to the same scale and integer width,
        along with the common scale. Does not modify self or other.

        Returns:
            (a_digits, b_digits, common_scale)
        """
        common_scale = max(self.scale, other.scale)
        a = self.digits  + [0] * (common_scale - self.scale)
        b = other.digits + [0] * (common_scale - other.scale)

        a_int = len(a) - common_scale
        b_int = len(b) - common_scale
        max_int = max(a_int, b_int)
        a = [0] * (max_int - a_int) + a
        b = [0] * (max_int - b_int) + b

        return a, b, common_scale

    def _add_abs(self, other):
        """
        Returns (digits, scale) for |self| + |other|.
        Sign is not set here — the caller assigns it via _from_parts().
        """
        a, b, common_scale = self._align(other)

        result = [0] * len(a)
        carry  = 0
        for i in range(len(a) - 1, -1, -1):
            total      = a[i] + b[i] + carry
            result[i]  = total % 10
            carry      = total // 10
        if carry:
            result.insert(0, carry)

        return result, common_scale

    def _sub_abs(self, other):
        """
        Returns digits and scale for |self| - |other|.
        Assumes |self| >= |other| — the caller must ensure this.
        Sign is not set here — the caller assigns it.
        """
        a, b, common_scale = self._align(other)

        result = [0] * len(a)
        borrow = 0
        for i in range(len(a) - 1, -1, -1):
            diff      = a[i] - b[i] - borrow
            if diff < 0:
                diff   += 10
                borrow  = 1
            else:
                borrow  = 0
            result[i] = diff

        return result, common_scale

    def __add__(self, other):
        """
        Returns a new DecimalNumber equal to self + other.
        The result scale is max(self.scale, other.scale) — exact, no rounding.
        """
        if not isinstance(other, DecimalNumber):
            return NotImplemented

        # Adding zero is a no-op
        if self.sign == 0:
            return DecimalNumber._from_parts(other.sign, other.digits, other.scale)
        if other.sign == 0:
            return DecimalNumber._from_parts(self.sign, self.digits, self.scale)

        if self.sign == other.sign:
            # Same sign: add absolute values, keep the sign
            digits, scale = self._add_abs(other)
            return DecimalNumber._from_parts(self.sign, digits, scale)
        else:
            # Opposite signs: subtract the smaller from the larger
            cmp = self._compare_abs(other)
            if cmp == 0:
                return DecimalNumber._from_parts(0, [0], 0)
            elif cmp > 0:
                # |self| > |other| → result takes self's sign
                digits, scale = self._sub_abs(other)
                return DecimalNumber._from_parts(self.sign, digits, scale)
            else:
                # |self| < |other| → result takes other's sign
                digits, scale = other._sub_abs(self)
                return DecimalNumber._from_parts(other.sign, digits, scale)

    def __sub__(self, other):
        """
        Returns a new DecimalNumber equal to self - other.
        Implemented as self + (-other).
        """
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        negated = DecimalNumber._from_parts(-other.sign, other.digits, other.scale)
        return self.__add__(negated)

    def __mul__(self, other):
        """
        Returns a new DecimalNumber equal to self * other.

        Algorithm: schoolbook digit-by-digit multiplication on the integer
        representations, then reposition the decimal point.

        The result scale is self.scale + other.scale (exact, no rounding).
        Apply quantize() afterwards if a reduced scale is needed.
        """
        if not isinstance(other, DecimalNumber):
            return NotImplemented

        # 0 * anything = 0
        if self.sign == 0 or other.sign == 0:
            return DecimalNumber._from_parts(0, [0], 0)

        result_sign  = self.sign * other.sign
        result_scale = self.scale + other.scale

        a = self.digits
        b = other.digits

        # Allocate result array: at most len(a) + len(b) digits
        result = [0] * (len(a) + len(b))

        # Schoolbook multiplication, right-to-left on both operands
        for i in range(len(a) - 1, -1, -1):
            for j in range(len(b) - 1, -1, -1):
                pos        = i + j + 1
                product    = a[i] * b[j]
                total      = result[pos] + product
                result[pos]     = total % 10
                result[pos - 1] += total // 10  # carry may exceed 9 temporarily

        # Final normalization pass: ensure no cell exceeds 9
        # (carries from the inner loop may have accumulated)
        carry = 0
        for i in range(len(result) - 1, -1, -1):
            total      = result[i] + carry
            result[i]  = total % 10
            carry      = total // 10
        if carry:
            result.insert(0, carry)

        return DecimalNumber._from_parts(result_sign, result, result_scale)

    def divide(self, other, scale, mode):
        """
        Returns a new DecimalNumber equal to self / other, rounded to `scale`
        decimal places using `mode`.

        Unlike +, -, *, division cannot always produce an exact finite result
        (e.g. 1/3 = 0.333...), so a target scale and rounding mode are mandatory.

        Algorithm: integer arithmetic via Python's arbitrary-precision int.
          1. Convert self and other to their integer representations A and B
             (i.e. the digit lists interpreted as integers, ignoring the decimal
             point).
          2. Scale A by a power of 10 so that the integer quotient A//B has
             exactly (scale + 1) fractional digits — the extra digit is the
             guard digit used for rounding.
          3. Perform the division as a single Python integer floor-division,
             then convert the quotient back to a digit list.
          4. Delegate rounding to apply_rounding() to obtain the final
             `scale`-digit result.

        Note: this approach relies on Python's built-in arbitrary-precision
        integers rather than operating digit-by-digit on the internal lists.
        This is a deliberate simplification appropriate for this implementation.

        Args:
            other (DecimalNumber) : divisor
            scale (int)           : number of fractional digits in the result, >= 0
            mode  (str)           : one of the ROUND_* constants from rounding.py

        Returns:
            DecimalNumber

        Raises:
            ZeroDivisionError : if other is zero
            ValueError        : if scale < 0 or mode is unknown
        """
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        if other.sign == 0:
            raise ZeroDivisionError("Division par zéro")
        if not isinstance(scale, int) or scale < 0:
            raise ValueError(f"scale doit être un entier >= 0, reçu : {scale}")
        if mode not in _ALL_MODES:
            raise ValueError(f"Mode d'arrondi inconnu : {mode}")

        # Dividend is zero → result is zero
        if self.sign == 0:
            return DecimalNumber._from_parts(0, [0], 0)

        result_sign = self.sign * other.sign

        # Work with the integer representations (ignore decimal points).
        # self  = A * 10^(-self.scale)   → integer A = self.digits as number
        # other = B * 10^(-other.scale)  → integer B = other.digits as number
        # self / other = (A / B) * 10^(other.scale - self.scale)
        #
        # We want `scale` fractional digits in the result, so we need to
        # produce the integer quotient of:
        #   A * 10^(scale + other.scale - self.scale + 1)  divided by  B
        # (+1 for the guard digit used in rounding)
        #
        # If the exponent is negative (other.scale < self.scale - scale - 1),
        # we shift B instead to avoid multiplying A by a fraction.

        exponent = scale - self.scale + other.scale + 1  # extra digits to compute

        # Build integer dividend and divisor as plain Python ints
        def digits_to_int(d):
            n = 0
            for digit in d:
                n = n * 10 + digit
            return n

        dividend = digits_to_int(self.digits)
        divisor  = digits_to_int(other.digits)

        if exponent >= 0:
            dividend *= 10 ** exponent
        else:
            divisor  *= 10 ** (-exponent)

        # Long division: extract (scale + 1) digits of quotient
        # We work digit by digit to stay in pure integer arithmetic.
        quotient_digits = []
        remainder = 0
        # Convert dividend to a digit list for long division
        dividend_digits = [int(c) for c in str(dividend)]

        for d in dividend_digits:
            remainder = remainder * 10 + d
            q = remainder // divisor
            remainder = remainder % divisor
            quotient_digits.append(q)

        # If dividend_digits was shorter than needed, extend with zeros
        # (this happens when dividend < divisor for the first several steps)
        # The above loop already handles this naturally through remainder.

        # Ensure we have exactly (scale + 1) digits of quotient.
        # The integer part of the result may have more digits — we only
        # round the fractional tail, so we keep all integer digits plus
        # (scale + 1) fractional digits total.
        #
        # quotient_digits currently holds the full integer quotient of the
        # scaled division. Its last (scale + 1) digits are the fractional
        # part (including guard). We pass the whole list to apply_rounding
        # with new_scale = scale.
        raw_scale  = scale + 1   # scale of quotient_digits as a decimal number
        new_digits = apply_rounding(
            quotient_digits, raw_scale, scale, result_sign, mode
        )

        return DecimalNumber._from_parts(result_sign, new_digits, scale)

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def _compare(self, other):
        """
        Full signed comparison of self and other.

        Returns:
             1  if self > other
             0  if self == other
            -1  if self < other
        """
        # Different signs cover most cases immediately
        if self.sign != other.sign:
            return 1 if self.sign > other.sign else -1

        # Both zero
        if self.sign == 0:
            return 0

        # Same sign: compare absolute values, then apply sign
        cmp_abs = self._compare_abs(other)
        if self.sign == 1:
            return cmp_abs          # positive: larger absolute → larger value
        else:
            return -cmp_abs         # negative: larger absolute → smaller value

    def __eq__(self, other):
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        return self._compare(other) == 0

    def __lt__(self, other):
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        return self._compare(other) < 0

    def __le__(self, other):
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        return self._compare(other) <= 0

    def __gt__(self, other):
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        return self._compare(other) > 0

    def __ge__(self, other):
        if not isinstance(other, DecimalNumber):
            return NotImplemented
        return self._compare(other) >= 0

    # ------------------------------------------------------------------
    # String representations
    # ------------------------------------------------------------------

    def __str__(self):
        """Human-readable representation — same as get()."""
        return self.get()

    def __repr__(self):
        """Unambiguous representation, useful in the REPL and for debugging."""
        return f"DecimalNumber('{self.get()}')"

    def get(self):
        """Returns the string representation at active_scale."""
        value = '-' if self.sign == -1 else ''

        # Pad with trailing zeros up to active_scale if needed
        display_digits = self.digits + [0] * (self.active_scale - self.scale)

        count = 0
        for digit in display_digits:
            if len(display_digits) - self.active_scale == count and self.active_scale > 0:
                value += '.'
            value += str(digit)
            count += 1
        return value


