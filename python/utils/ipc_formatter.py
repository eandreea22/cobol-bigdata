#!/usr/bin/env python3
"""
IPC Formatter: Convert Python data types to COBOL fixed-width record formats.

These two functions are the foundation of the COBOL-Python IPC contract.
All output from Python analytics scripts must use these to ensure byte-perfect
alignment with COBOL copybook PIC clauses.
"""


def format_pic_x(value: str, length: int) -> str:
    """
    Format a string value as COBOL PIC X (alphanumeric).

    Left-justified, space-padded, truncated to exactly `length` characters.

    Args:
        value: String to format (or any object convertible to string)
        length: Target field length

    Returns:
        Formatted string of exactly `length` characters

    Examples:
        format_pic_x("John", 50) -> "John" + " "*46  (50 chars total)
        format_pic_x("A"*60, 50) -> "A"*50  (truncated)
    """
    return str(value).ljust(length)[:length]


def format_pic_9(value: float, integer_digits: int, decimal_digits: int = 0) -> str:
    """
    Format a numeric value as COBOL PIC 9 (numeric).

    Right-justified, zero-padded, with an implied decimal point (no actual
    decimal character in output). Negative values are converted to absolute value.

    Args:
        value: Numeric value to format
        integer_digits: Number of digits before the (implied) decimal point
        decimal_digits: Number of digits after the (implied) decimal point (default 0)

    Returns:
        Formatted numeric string of exactly (integer_digits + decimal_digits) characters

    Examples:
        format_pic_9(1234.56, 10, 2) -> "000000123456"  (12 chars: 10+2)
        format_pic_9(4.75, 1, 4) -> "04750"  (5 chars: 1+4)
        format_pic_9(0, 3) -> "000"  (3 chars)
        format_pic_9(1000, 3) -> "100"  (overflow: truncated to fit)
        format_pic_9(-50.5, 5, 2) -> "00005050"  (8 chars: negation ignored)
    """
    total = integer_digits + decimal_digits
    # Scale the value: multiply by 10^decimal_digits to shift decimal point
    # Use abs() because COBOL PIC 9 is unsigned
    scaled = int(abs(value) * (10 ** decimal_digits))
    # Convert to zero-padded string, then truncate to total width
    return str(scaled).zfill(total)[:total]
