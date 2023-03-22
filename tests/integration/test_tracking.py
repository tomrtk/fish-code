"""Integration tests for interfacing with tracking."""
from datetime import datetime

import pytest

from core import interface
from core.model import BBox, Detection, Frame, Object


@pytest.fixture
def make_frames() -> list[Frame]:
    """Return a list of valid frames."""
    frames = [
        Frame(
            0,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 0),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 0),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 0),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 0),
            ],
            datetime(1, 1, 1, 1, 1, 1),
        ),
        Frame(
            1,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 1),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 1),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 1),
            ],
            datetime(1, 1, 1, 1, 1, 2),
        ),
        Frame(
            2,
            [
                Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 2),
                Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 2),
                Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 2),
                Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 2),
            ],
            datetime(1, 1, 1, 1, 1, 3),
        ),
    ]
    return frames


@pytest.mark.usefixtures("tracing_api")
def test_to_track(make_frames: list[Frame]):
    """Test to see values returned from to_track are valid."""
    frames = make_frames

    objects = interface.to_track(frames)

    assert objects is not None
    assert isinstance(objects[0], Object)
    assert isinstance(objects[0]._detections[0], Detection)
    assert isinstance(objects[0]._detections[0].bbox, BBox)
