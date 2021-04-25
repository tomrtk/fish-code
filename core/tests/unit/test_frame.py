"""Unmit tests for Frame."""
from datetime import datetime

from core.model import BBox, Detection, Frame


def test_frame_to_json():
    """Test frame to json."""
    date = datetime(2020, 3, 28, 10, 20, 30)
    frame = Frame(1, [Detection(BBox(10, 20, 30, 40), 0.8, 1, 1)], date)

    assert frame.to_json() == {
        "idx": 1,
        "detections": [frame.detections[0].to_json()],
        "timestamp": date.isoformat(),
        "video_id": None,
    }

    frame = Frame(2, [Detection(BBox(10, 20, 30, 40), 0.8, 1, 1)], video_id=3)

    assert frame.to_json() == {
        "idx": 2,
        "detections": [frame.detections[0].to_json()],
        "timestamp": None,
        "video_id": 3,
    }


def test_frame_eq():
    """Test equality between frame."""
    fr1 = Frame(
        1,
        [
            Detection(BBox(10, 20, 30, 40), 0.9, 1, 1),
            Detection(BBox(100, 200, 300, 400), 0.9, 1, 1),
        ],
    )

    fr2 = Frame(
        1,
        [
            Detection(BBox(10, 20, 30, 40), 0.9, 1, 1),
            Detection(BBox(100, 200, 300, 400), 0.9, 1, 1),
        ],
        video_id=8,
    )

    fr3 = Frame(
        1,
        [
            Detection(BBox(50, 60, 70, 80), 0.9, 2, 1),
        ],
        video_id=8,
    )

    assert fr1 != fr2
    assert fr2 == fr3
    fr1.video_id = 8
    assert fr1 == fr2
    fr2.detections.append(Detection(BBox(99, 99, 99, 99), 0.3, 3, 21))
    assert fr2 == fr3
    assert fr1 != "Some random data"
