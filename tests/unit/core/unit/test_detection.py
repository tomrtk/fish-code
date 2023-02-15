"""Unit test for Detection."""
import pytest

from core.model import BBox, Detection


@pytest.fixture()
def make_detection():
    """Create a detection object."""
    return Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1)


def test_detection__init__():
    """Test Detection creation."""
    _ = Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1)

    with pytest.raises(TypeError):
        _ = Detection(BBox(*[10, 20, 30, 40, 50]), 1.0, 1, 1)

    with pytest.raises(TypeError):
        _ = Detection(BBox(*[10, 20, 30]), 1.0, 1, 1)


def test_set_frame(make_detection):
    """Set frame number."""
    det = make_detection
    det = det.set_frame(2, 1, 1)

    assert det.frame == 2
