import numpy as np
import pytest

from tracing.tracker import BBox


### Bounding Box BBox ###
@pytest.fixture
def bbox_list():
    return [10.0, 10.0, 10.0, 10.0]


def test_bbox_init(bbox_list):
    bbox = BBox(*bbox_list)

    assert bbox_list[0] == bbox.x1
    assert bbox_list[1] == bbox.y1
    assert bbox_list[2] == bbox.x2
    assert bbox_list[3] == bbox.y2


def test_bbox_to_list(bbox_list):
    bbox = BBox(*bbox_list)

    np.testing.assert_allclose(bbox.to_list(), bbox_list)


def test_bbox_from_list(bbox_list):
    bbox = BBox.from_list(bbox_list)

    assert bbox_list[0] == bbox.x1
    assert bbox_list[1] == bbox.y1
    assert bbox_list[2] == bbox.x2
    assert bbox_list[3] == bbox.y2


def test_bbox_from_xywh(bbox_list):
    bbox = BBox.from_xywh(bbox_list)

    np.testing.assert_allclose([10, 10, 20, 20], bbox.to_list())


def test_bbox__eq__same(bbox_list):
    bbox = BBox(*bbox_list)
    other_bbox = BBox(*bbox_list)
    assert bbox == other_bbox


def test_bbox__eq__over_tolerance(bbox_list):
    bbox = BBox(*bbox_list)

    tol = 0.11

    other_bbox = BBox(*bbox_list)
    other_bbox.x1 += tol
    other_bbox.y1 += tol
    other_bbox.x2 += tol
    other_bbox.y2 += tol
    assert not bbox == other_bbox


def test_bbox__eq__under_tolerance(bbox_list):
    bbox = BBox(*bbox_list)

    tol = 0.11
    other_bbox = BBox(*bbox_list)
    other_bbox.x1 -= tol
    other_bbox.y1 -= tol
    other_bbox.x2 -= tol
    other_bbox.y2 -= tol
    assert not bbox == other_bbox


def test_bbox_to_dict(bbox_list):
    assert {
        "x1": 10.0,
        "y1": 10.0,
        "x2": 10.0,
        "y2": 10.0,
    } == BBox.from_list(bbox_list).to_dict()
