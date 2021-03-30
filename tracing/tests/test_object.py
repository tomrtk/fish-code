"""Unit tests of Object."""
import copy

import pytest

from tracing.tracker import BBox, Detection, Object


@pytest.fixture
def bbox():
    """Return a valid bbox."""
    return BBox(*[10, 20, 30, 40])


@pytest.fixture
def detection(bbox):
    """Return a valid detection."""
    return Detection(bbox, 1, 1.0, 1)


def test_object_update(detection):
    """Test object update."""
    obj = Object(1)
    other_detection = copy.copy(detection)
    other_detection.frame = 2
    obj.update(other_detection)

    assert obj.label == 1


def test_object_update_other(detection):
    """Test object with other label."""
    obj = Object(1)

    obj.update(detection)

    assert obj.label == detection.label

    other_label = 69
    other_detection = copy.copy(detection)
    other_detection.label = other_label
    other_detection.frame = 2
    obj.update(other_detection)

    other_detection = copy.copy(detection)
    other_detection.label = other_label
    other_detection.frame = 3
    obj.update(other_detection)

    assert obj.label == other_label


def test_object_update_same(detection):
    """Test object update same label."""
    obj = Object(1)

    obj.update(detection)

    with pytest.raises(ValueError):
        obj.update(detection)


def test_object_to_dict(detection):
    """Test object to dict."""
    obj = Object(1)

    obj.update(detection)

    assert {
        "track_id": 1,
        "detections": [
            {
                "bbox": {
                    "x1": 10.0,
                    "y1": 20.0,
                    "x2": 30.0,
                    "y2": 40.0,
                },
                "label": 1,
                "probability": 1.0,
                "frame": 1,
            },
        ],
        "label": 1,
    } == obj.to_dict()


def test_object_to_dict_no_detect():
    """Test object to dict with no detect."""
    obj = Object(1)

    assert {
        "track_id": 1,
        "detections": [],
        "label": None,
    } == obj.to_dict()
