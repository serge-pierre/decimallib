# Rounding modes
#
# Geometric modes (no notion of "halfway"):
ROUND_TRUNC   = 'ROUND_TRUNC'    # Toward zero (truncate)  :  1.9 → 1,   -1.9 → -1
ROUND_FLOOR   = 'ROUND_FLOOR'    # Toward -∞               :  1.9 → 1,   -1.1 → -2
ROUND_CEIL    = 'ROUND_CEIL'     # Toward +∞               :  1.1 → 2,   -1.9 → -1
#
# Halfway modes (behavior differs only at exactly 0.5):
ROUND_HALF_UP          = 'ROUND_HALF_UP'          # 0.5 toward +∞              :  1.5 → 2,   -1.5 → -1
ROUND_HALF_TOWARD_ZERO = 'ROUND_HALF_TOWARD_ZERO' # 0.5 toward zero            :  1.5 → 1,   -1.5 → -1
ROUND_HALF_AWAY_ZERO   = 'ROUND_HALF_AWAY_ZERO'   # 0.5 away from zero         :  1.5 → 2,   -1.5 → -2
ROUND_HALF_EVEN        = 'ROUND_HALF_EVEN'        # 0.5 toward nearest even    :  0.5 → 0,    1.5 → 2
ROUND_HALF_PROPORTIONAL= 'ROUND_HALF_PROPORTIONAL'# 0.5 by digit-sum parity    :  deterministic, ~50/50

_ALL_MODES = {
    ROUND_TRUNC, ROUND_FLOOR, ROUND_CEIL,
    ROUND_HALF_UP, ROUND_HALF_TOWARD_ZERO, ROUND_HALF_AWAY_ZERO,
    ROUND_HALF_EVEN, ROUND_HALF_PROPORTIONAL,
}

def apply_rounding(digits, scale, new_scale, sign, mode):
    """
    Rounds a number represented as (digits, scale, sign) to new_scale.

    Args:
        digits    (list[int]) : digits of the number, most significant first
                                e.g. [1, 2, 3, 4, 5] for 123.45 at scale=2
        scale     (int)       : current scale
        new_scale (int)       : target scale (must be < scale)
        sign      (int)       : -1, 0, or 1
        mode      (str)       : one of the ROUND_* constants

    Returns:
        list[int]: new digits list at new_scale (before trailing/leading zero cleanup)
    """
    if mode not in _ALL_MODES:
        raise ValueError(f"Mode d'arrondi inconnu : {mode}")

    # Work on a copy
    digits = list(digits)

    # Split: kept digits vs dropped digits
    drop = scale - new_scale
    cut  = len(digits) - drop

    kept    = digits[:cut]
    dropped = digits[cut:]

    # Guard digit: first dropped digit (determines the "half" boundary)
    guard        = dropped[0] if dropped else 0
    tail         = dropped[1:] if len(dropped) > 1 else []
    tail_nonzero = any(d != 0 for d in tail)
    has_remainder = guard > 0 or tail_nonzero

    # Is the dropped part exactly half (0.5 * step)?
    exactly_half = (guard == 5 and not tail_nonzero)
    above_half   = (guard > 5) or (guard == 5 and tail_nonzero)

    increment = False

    # --- Geometric modes ---

    if mode == ROUND_TRUNC:
        increment = False

    elif mode == ROUND_FLOOR:
        # Toward -∞: increment the absolute value only if negative
        increment = (sign == -1) and has_remainder

    elif mode == ROUND_CEIL:
        # Toward +∞: increment the absolute value only if positive
        increment = (sign == 1) and has_remainder

    # --- Halfway modes ---

    elif mode == ROUND_HALF_UP:
        # 0.5 toward +∞: for positives, .5 increments; for negatives, .5 does not
        if exactly_half:
            increment = (sign == 1)
        else:
            increment = above_half

    elif mode == ROUND_HALF_TOWARD_ZERO:
        # 0.5 toward zero: .5 never increments (regardless of sign)
        increment = above_half

    elif mode == ROUND_HALF_AWAY_ZERO:
        # 0.5 away from zero: .5 always increments (regardless of sign)
        increment = above_half or exactly_half

    elif mode == ROUND_HALF_EVEN:
        # Banker's rounding: .5 rounds toward the nearest even digit
        last_kept = kept[-1] if kept else 0
        if exactly_half:
            increment = (last_kept % 2 != 0)  # round to even
        else:
            increment = above_half

    elif mode == ROUND_HALF_PROPORTIONAL:
        # Deterministic ~50/50: .5 rounds based on parity of digit sum of quotient
        if exactly_half:
            digit_sum = sum(kept)
            increment = (digit_sum % 2 != 0)
        else:
            increment = above_half

    # --- Apply increment with carry propagation ---
    if increment:
        carry = 1
        for i in range(len(kept) - 1, -1, -1):
            total   = kept[i] + carry
            kept[i] = total % 10
            carry   = total // 10
        if carry:
            kept.insert(0, carry)  # e.g. 9.99 → 10.00

    return kept
