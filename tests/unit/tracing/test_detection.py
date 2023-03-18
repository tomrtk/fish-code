"""Unit tests for detection class."""
import pytest

from tracing.tracker import BBox, Detection


@pytest.fixture
def detection() -> Detection:
    """Return a valid detection."""
    return Detection(
        BBox(*[10, 10, 10, 10]),
        label=1,
        probability=1.0,
        frame=1,
        frame_id=2,
        video_id=3,
        true_track_id=1,
    )


@pytest.fixture
def detection_json():
    """Return detection as json."""
    return {
        "bbox": {
            "x1": 10.0,
            "y1": 10.0,
            "x2": 10.0,
            "y2": 10.0,
        },
        "label": 1,
        "probability": 1.0,
        "frame_id": 2,
        "video_id": 3,
        "frame": 1,
    }


def test_detection_to_dict(detection, detection_json):
    """Test detection to_dict."""
    assert detection_json == detection.to_dict()


def test_detection_from_dict(detection, detection_json):
    """Test detection from_dict."""
    assert Detection.from_dict(detection_json).to_dict() == detection.to_dict()


def test_detection_from_dict_miss_element(detection):
    """Test detection from_dict with missing element."""
    json_wrong = {
        "bbox": {
            "x1": 10.0,
            "y1": 10.0,
            "x2": 10.0,
            "y2": 10.0,
        },
        "probability": 1.0,
        "frame": 1,
    }
    with pytest.raises(KeyError):
        Detection.from_dict(json_wrong).to_dict() == detection.to_dict()


def test_detection_from_api_miss_element(detection):
    """Test detection from api with missing element."""
    json_wrong = {
        "bbox": {
            "x1": 10.0,
            "y1": 10.0,
            "x2": 10.0,
            "y2": 10.0,
        },
        "probability": 1.0,
    }
    with pytest.raises(KeyError):
        Detection.from_api(json_wrong, 1).to_dict() == detection.to_dict()
