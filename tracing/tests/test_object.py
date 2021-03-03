import pytest

from tracing.tracker import BBox, Detection, Object


@pytest.fixture
def bbox():
    return BBox(*[10, 10, 10, 10])


@pytest.fixture
def detection(bbox):
    return Detection(bbox, 1, 1.0, 1)


def test_object_update_same(detection):
    obj = Object(1)
    other_detection = detection
    other_detection.frame = 2
    obj.update(other_detection)

    assert obj.label == 1


def test_object_update_other(detection):
    obj = Object(1)

    obj.update(detection)

    other_label = 69
    other_detection = detection
    other_detection.label = other_label
    other_detection.frame = 2
    obj.update(other_detection)

    other_detection = detection
    other_detection.label = other_label
    other_detection.frame = 3
    obj.update(other_detection)

    assert obj.label == other_label


def test_object_to_dict(detection):

    obj = Object(1)

    obj.update(detection)

    assert {
        "track_id": 1,
        "detections": [
            {
                "bbox": {
                    "x1": 10.0,
                    "y1": 10.0,
                    "x2": 10.0,
                    "y2": 10.0,
                },
                "label": 1,
                "score": 1.0,
                "frame": 1,
            },
        ],
        "label": 1,
    } == obj.to_dict()
