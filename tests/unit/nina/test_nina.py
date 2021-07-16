"""Tests for nina."""
import nina


def test_import_works() -> None:
    """Test import of `nina` working."""
    assert isinstance(nina.__version__, str)
