"""Unit test for Detection."""
import pytest

from core.model import BBox, Detection


def test_detection__init__():
    """Test Detection creation."""
    det = Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1)

    with pytest.raises(TypeError):
        det = Detection(BBox(*[10, 20, 30, 40, 50]), 1.0, 1, 1)

    with pytest.raises(TypeError):
        det = Detection(BBox(*[10, 20, 30]), 1.0, 1, 1)
