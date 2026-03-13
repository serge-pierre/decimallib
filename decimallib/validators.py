import re

# The regex is compiled ONLY ONCE at the module level.
#
# Rule: at least one digit must be present somewhere.
# We use two alternatives to express this cleanly:
#   \d+\.?\d*   a digit before the point  (e.g. "123", "123.", "123.45")
#   \d*\.\d+    a digit after  the point  (e.g. ".45", "0.45")
#
# ^[+-]?(\d+\.?\d*|\d*\.\d+)$
# │└──┬─┘└────────┬─────────┘│
# │   │           │           └─ $ : end of string
# │   │           └───────────── at least one digit, optional point
# │   └───────────────────────── [+-]? : optional sign
# └───────────────────────────── ^ : start of string
#
# Rejected by this regex: "", ".", "+", "-", "+.", "-."
_PATTERN_NUMBER = re.compile(r'^[+-]?(\d+\.?\d*|\d*\.\d+)$')


def is_number_valid(string):
    """
    Checks whether a string is a valid decimal number.

    Rules:
    - An optional + or - sign at the beginning
    - An optional decimal point (maximum one)
    - At least one digit somewhere (before or after the decimal point)

    Accepted  : "0", "123", "-45.6", "+.5", "123.", ".123", "000.000"
    Rejected  : "", ".", "+", "-", "+.", "abc", "1.2.3"

    Args:
        string (str): The string to validate

    Returns:
        bool: True if the string is valid, False otherwise
    """
    if not isinstance(string, str):
        return False

    return _PATTERN_NUMBER.match(string) is not None


def get_scale(unsigned_number):
    """
    Determines the number of digits after the decimal point.

    Args:
        unsigned_number (str): String representing a number without sign,
                               already normalized (never just "." alone).
                               Examples: '123', '123.45', '.123', '123.'

    Returns:
        int: Number of digits after the decimal point
             (0 if there is no decimal point or nothing after it)

    Examples:
        >>> get_scale('123')
        0
        >>> get_scale('123.45')
        2
        >>> get_scale('.123')
        3
        >>> get_scale('123.')
        0
        >>> get_scale('0')
        0
    """
    if '.' not in unsigned_number:
        return 0

    part_after_point = unsigned_number.split('.')[1]
    return len(part_after_point)
