"""Unit test of bounding box."""
from typing import List

import numpy as np
import pytest

from tracing.tracker import BBox


### Bounding Box BBox ###
@pytest.fixture
def bbox_list() -> list[float]:
    """Create a list for creating BBox.

    Return
    ------
    List[float]
        A list that BBox accepts.
    """
    return [10.0, 20.0, 30.0, 40.0]


def test_bbox_init(bbox_list):
    """Test bbox constructor."""
    bbox = BBox(*bbox_list)

    assert bbox_list[0] == bbox.x1
    assert bbox_list[1] == bbox.y1
    assert bbox_list[2] == bbox.x2
    assert bbox_list[3] == bbox.y2


def test_bbox_to_list(bbox_list):
    """Test bbox to list."""
    bbox = BBox(*bbox_list)

    np.testing.assert_allclose(bbox.to_list(), bbox_list)
    assert isinstance(bbox.to_list(), list)


def test_bbox_from_list(bbox_list):
    """Test bbox from list."""
    bbox = BBox.from_list(bbox_list)

    assert bbox_list[0] == bbox.x1
    assert bbox_list[1] == bbox.y1
    assert bbox_list[2] == bbox.x2
    assert bbox_list[3] == bbox.y2


def test_bbox_from_list_five():
    """Test bbox from list with five elements."""
    with pytest.raises(ValueError):
        bbox = BBox.from_list([10, 10, 10, 10, 10])


def test_bbox_from_list_three():
    """Test bbox from list with three elements."""
    with pytest.raises(ValueError):
        bbox = BBox.from_list([10, 10, 10])


def test_bbox_from_xywh(bbox_list):
    """Test bbox from xywh."""
    bbox = BBox.from_xywh(bbox_list)

    np.testing.assert_allclose([10, 20, 40, 60], bbox.to_list())


def test_bbox_from_xywh_five():
    """Test bbox from xywh with five elements."""
    with pytest.raises(ValueError):
        bbox = BBox.from_xywh([10, 10, 10, 10, 10])


def test_bbox_from_xywh_three():
    """Test bbox from xywh with three elements."""
    with pytest.raises(ValueError):
        bbox = BBox.from_xywh([10, 10, 10])


def test_bbox__eq__same(bbox_list):
    """Test bbox eq with equal elements."""
    bbox = BBox(*bbox_list)
    other_bbox = BBox(*bbox_list)
    assert bbox == other_bbox
    assert bbox == bbox

    tol = 0.009  # Less than one percent difference should be considered equal
    other_bbox.x1 -= bbox.x1 * tol
    other_bbox.y1 -= bbox.y1 * tol
    other_bbox.x2 -= bbox.x2 * tol
    other_bbox.y2 -= bbox.y2 * tol

    assert bbox == other_bbox

    other_bbox.x1 += bbox.x1 * tol
    other_bbox.y1 += bbox.y1 * tol
    other_bbox.x2 += bbox.x2 * tol
    other_bbox.y2 += bbox.y2 * tol

    assert bbox == other_bbox


def test_bbox__eq__not_same(bbox_list):
    """Test bbox eq with unequal elements."""
    bbox = BBox(*bbox_list)

    tol = (
        0.011  # More than one percent difference should be considered not equal
    )
    other_bbox = BBox(*bbox_list)
    other_bbox.x1 += bbox.x1 * tol
    other_bbox.y1 += bbox.y1 * tol
    other_bbox.x2 += bbox.x2 * tol
    other_bbox.y2 += bbox.y2 * tol
    assert not bbox == other_bbox

    other_bbox = BBox(*bbox_list)
    other_bbox.x1 -= bbox.x1 * tol
    other_bbox.y1 -= bbox.y1 * tol
    other_bbox.x2 -= bbox.x2 * tol
    other_bbox.y2 -= bbox.y2 * tol
    assert not bbox == other_bbox


def test_bbox_to_dict(bbox_list):
    """Test bbox to dict."""
    assert {
        "x1": 10.0,
        "y1": 20.0,
        "x2": 30.0,
        "y2": 40.0,
    } == BBox.from_list(bbox_list).to_dict()
    assert isinstance(BBox.from_list(bbox_list).to_dict(), dict)
