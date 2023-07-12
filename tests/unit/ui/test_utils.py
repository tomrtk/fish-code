"""Unit test of ui utils functions."""
import pytest
from pydantic.error_wrappers import ValidationError

from ui.projects.utils import SQLITE_INTEGER_LIMIT, validate_int


def test_validate_int() -> None:
    """Test int validation."""
    assert validate_int(0) == 0
    assert validate_int(-(2**64)) is None
    assert validate_int(2**64) is None
    assert validate_int(SQLITE_INTEGER_LIMIT - 1) is not None
    assert validate_int(-SQLITE_INTEGER_LIMIT + 1) is not None

    with pytest.raises(ValidationError):
        _ = validate_int("test")  # type: ignore

    with pytest.raises(ValidationError):
        _ = validate_int(b"test")  # type: ignore
