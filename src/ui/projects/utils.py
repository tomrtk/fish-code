"""Utilities functions used in ui."""
from typing import Optional

from pydantic import validate_arguments

SQLITE_INTEGER_LIMIT = 2 ** 63 - 1


@validate_arguments
def validate_int(
    number: int,
    min_value: int = -SQLITE_INTEGER_LIMIT,
    max_value: int = SQLITE_INTEGER_LIMIT,
) -> Optional[int]:
    """Validate number to be an int within min and max inclusive."""
    num = int(number)

    if isinstance(num, int) and num < min_value or num > max_value:
        return None

    return num
