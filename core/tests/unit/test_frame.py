from datetime import datetime

from core.model import BBox, Detection, Frame


def test_frame_to_json():

    date = datetime(2020, 3, 28, 10, 20, 30)
    frame = Frame(1, [Detection(BBox(10, 20, 30, 40), 0.8, 1, 1)], date)

    assert frame.to_json() == {
        "idx": 1,
        "detections": [frame.detections[0].to_json()],
        "timestamp": date.isoformat(),
    }

    date = None
    frame = Frame(1, [Detection(BBox(10, 20, 30, 40), 0.8, 1, 1)], date)

    assert frame.to_json() == {
        "idx": 1,
        "detections": [frame.detections[0].to_json()],
        "timestamp": None,
    }
