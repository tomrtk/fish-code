"""Interface tests between `core` and `detection` API."""
import pytest
import numpy as np
from pathlib import Path

import core.interface as interface
from core.model import BBox, Detection, Frame, Video

TEST_VIDEO_PATH = Path(
    "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000.mp4"
)


@pytest.fixture
def make_images() -> np.ndarray:
    """Make a numpy array of many frames from test video."""
    return Video.from_path(str(TEST_VIDEO_PATH.resolve()))[0:10]


@pytest.fixture
def make_image() -> np.ndarray:
    """Make a numpy array of one frame from test video."""
    return Video.from_path(str(TEST_VIDEO_PATH.resolve()))[0]  # type: ignore


@pytest.mark.usefixtures("detection_api")
def test_detection_api_interface(
    make_images: np.ndarray, make_image: np.ndarray
):
    """Test detection interface in core with detection api."""
    frames = make_images
    detection_interface = interface.Detector()
    model_name = detection_interface.available_models[0].name

    # Test detecting with many frames
    frames = detection_interface.predict(frames, model_name)

    assert len(frames) == 10
    assert isinstance(frames[0], Frame)
    assert isinstance(frames[0].detections[0], Detection)
    assert isinstance(frames[0].detections[0].bbox, BBox)

    # Test detecting with one frame
    frame = make_image

    frame = detection_interface.predict(frame, model_name)
    assert len(frame) == 1
    assert isinstance(frame[0], Frame)
    assert isinstance(frame[0].detections[0], Detection)
    assert isinstance(frame[0].detections[0].bbox, BBox)

    frame = make_image

    # Test wrong `model_name`
    with pytest.raises(KeyError):
        _ = detection_interface.predict(frame, "testy")

    # Test wrong `frames` dimensions.
    frame_2d = np.zeros((128, 64))
    with pytest.raises(NotImplementedError):
        _ = detection_interface.predict(frame_2d, model_name)

    frame_5d = np.zeros((2, 2, 128, 64, 3))
    with pytest.raises(NotImplementedError):
        _ = detection_interface.predict(frame_5d, model_name)
