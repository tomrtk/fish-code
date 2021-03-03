import numpy as np
import pytest

from tracing.tracker import BBox, Detection


@pytest.fixture
def detection():
    return Detection(BBox(*[10, 10, 10, 10]), 1, 1.0, 1)


@pytest.fixture
def detection_json():
    return {
        "bbox": {
            "x1": 10.0,
            "y1": 10.0,
            "x2": 10.0,
            "y2": 10.0,
        },
        "label": 1,
        "score": 1.0,
        "frame": 1,
    }


def test_detection_to_SORT(detection):
    np.testing.assert_allclose(
        detection.to_SORT(),
        [
            detection.bbox.x1,
            detection.bbox.y1,
            detection.bbox.x2,
            detection.bbox.y2,
            detection.score,
        ],
    )


def test_detection_to_dict(detection, detection_json):
    assert detection_json == detection.to_dict()


def test_detection_from_dict(detection, detection_json):
    assert Detection.from_dict(detection_json).to_dict() == detection.to_dict()
