"""Unit test for SortTracker."""

import pytest

from tracing.tracker import BBox, Detection, SortTracker
from vendor.sort import sort


@pytest.fixture
def detection():
    """Return a valid detection."""
    return Detection(BBox(10, 20, 30, 40), 1, 1.0, 1, 1, 1, 1)


def test_convert(detection: Detection):
    """Test _connect_bb() statically and non-statically."""
    # static
    to_sort = SortTracker._convert(detection)

    assert to_sort[0] == detection.bbox.x1
    assert to_sort[1] == detection.bbox.y1
    assert to_sort[2] == detection.bbox.x2
    assert to_sort[3] == detection.bbox.y2
    assert to_sort[4] == detection.probability

    # non statically
    tracker = SortTracker(sort.Sort())
    to_sort = tracker._convert(detection)

    assert to_sort[0] == detection.bbox.x1
    assert to_sort[1] == detection.bbox.y1
    assert to_sort[2] == detection.bbox.x2
    assert to_sort[3] == detection.bbox.y2
    assert to_sort[4] == detection.probability
