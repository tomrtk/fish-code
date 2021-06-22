"""Unit testing interface to tracking and detection."""
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
from requests_mock.mocker import Mocker

from core.interface import Detector, to_track
from core.model import BBox, Detection, Frame, Object, Video

TEST_VIDEO_PATH = Path(__file__).parent / "test-[2020-03-28_12-30-10].mp4"
TEST_API_URI = "mock://127.0.0.1"
TEST_API_PORT = "9999"
TEST_API_URI_ERROR = "mock://127.0.0.2"


@pytest.fixture
def make_images() -> np.ndarray:
    """Make a numpy array of many frames from test video."""
    return Video.from_path(str(TEST_VIDEO_PATH.resolve()))[0:3]


@pytest.fixture
def make_image() -> np.ndarray:
    """Make a numpy array of many frames from test video."""
    return Video.from_path(str(TEST_VIDEO_PATH.resolve()))[0]


@pytest.fixture
def mock_to_track(requests_mock: Mocker):
    """Mock response from tracking api."""
    json_expected = [
        {
            "track_id": 0,
            "detections": [
                {
                    "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
                    "label": 0,
                    "probability": 0,
                    "frame": 0,
                    "frame_id": 0,
                    "video_id": 0,
                }
            ],
            "label": 0,
        }
    ]

    error = {"detail": [{"loc": ["string"], "msg": "string", "type": "string"}]}
    requests_mock.real_http = True  # type: ignore

    # mock status_codes not 200
    requests_mock.post(
        f"{TEST_API_URI_ERROR}:{TEST_API_PORT}/tracking/track",
        json=error,
        status_code=422,
    )
    # mock normal response
    requests_mock.post(
        f"{TEST_API_URI}:{TEST_API_PORT}/tracking/track", json=json_expected
    )
    return requests_mock


@pytest.fixture
def mock_detector(requests_mock: Mocker):
    """Mock response from detection api."""
    requests_mock.real_http = True  # type: ignore

    # mock status_codes not 200
    error = {"detail": [{"loc": ["string"], "msg": "string", "type": "string"}]}
    requests_mock.get(
        f"{TEST_API_URI_ERROR}:{TEST_API_PORT}/models/",
        json=error,
        status_code=422,
    )
    requests_mock.post(
        f"{TEST_API_URI_ERROR}:{TEST_API_PORT}/predictions/testy/",
        json=error,
        status_code=422,
    )

    # mock normal response from models endpoint
    requests_mock.get(
        f"{TEST_API_URI}:{TEST_API_PORT}/models/",
        json={
            "testy": [
                "test",
                "tester",
            ]
        },
    )

    # mock normal response with detections in each frame
    requests_mock.post(
        f"{TEST_API_URI}:{TEST_API_PORT}/predictions/testy/",
        json={
            1: [
                {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0,
                    "confidence": 0,
                    "label": 0,
                }
            ],
            2: [],
            3: [
                {
                    "x1": 0,
                    "y1": 0,
                    "x2": 0,
                    "y2": 0,
                    "confidence": 0,
                    "label": 0,
                }
            ],
        },
    )
    return requests_mock


def test_to_track(mock_to_track: Mocker):
    """Test tracking interface in core with mock tracking api."""
    _ = mock_to_track
    frames = [
        Frame(
            0,
            [
                Detection(BBox(*[0, 0, 0, 0]), 0.0, 0, 0),
            ],
            datetime(1, 1, 1, 1, 1, 1),
        ),
        Frame(
            1,
            [
                Detection(BBox(*[0, 0, 0, 0]), 0.0, 0, 0),
            ],
            None,
        ),
    ]

    resp = to_track(frames, host=TEST_API_URI, port=TEST_API_PORT)

    assert resp is not None

    assert isinstance(resp[0], Object)
    assert isinstance(resp[0]._detections[0], Detection)
    assert isinstance(resp[0]._detections[0].bbox, BBox)
    assert resp[0].track_id == 0
    assert resp[0].time_in is not None
    assert resp[0].time_out is not None

    resp = to_track(frames, host=TEST_API_URI_ERROR, port=TEST_API_PORT)
    assert len(resp) == 0


def test_detection_api_interface(
    mock_detector: Mocker,
    make_images: np.ndarray,
    make_image: np.ndarray,
):
    """Test detection interface in core with mock detection api."""
    _ = mock_detector
    detection_interface = Detector(host=TEST_API_URI, port=TEST_API_PORT)
    model_name = detection_interface.available_models[0].name

    # Test detecting with many frames
    frames = detection_interface.predict(make_images, model_name)

    assert len(frames) == 3
    assert isinstance(frames[0], Frame)
    assert isinstance(frames[0].detections[0], Detection)
    assert isinstance(frames[0].detections[0].bbox, BBox)

    # Test detecting with one frame
    frames = detection_interface.predict(make_image, model_name)
    assert len(frames) == 3

    # Test wrong `model_name`
    with pytest.raises(KeyError):
        _ = detection_interface.predict(make_images, "testyyy")

    # Test wrong `frames` dimensions.
    frame_2d = np.zeros((128, 64))
    with pytest.raises(NotImplementedError):
        _ = detection_interface.predict(frame_2d, model_name)

    frame_5d = np.zeros((2, 2, 128, 64, 3))
    with pytest.raises(NotImplementedError):
        _ = detection_interface.predict(frame_5d, model_name)


def test_detector_model_no_connection():
    """Test logic for no api connection."""
    with pytest.raises(ConnectionError):
        _ = Detector()


def test_detector_prediction_no_connection(
    mock_detector: Mocker, make_image: np.ndarray
):
    """Test logic for no api connection."""
    _ = mock_detector
    detection_interface = Detector(host=TEST_API_URI, port=TEST_API_PORT)
    model_name = detection_interface.available_models[0].name

    # change host to trigger connection error
    detection_interface.host = "http://nohost"

    with pytest.raises(ConnectionError):
        _ = detection_interface.predict(make_image, model_name)


def test_detector_model_not_status_code_200(
    mock_detector: Mocker,
):
    """Test detection interface model status_code handling."""
    _ = mock_detector
    detection_interface = Detector(host=TEST_API_URI, port=TEST_API_PORT)

    # change host to get status_code 422
    detection_interface.host = TEST_API_URI_ERROR

    result = detection_interface._models()

    assert len(result) == 0


def test_detection_prediction_not_status_code_200(
    mock_detector: Mocker,
    make_images: np.ndarray,
):
    """Test detection interface prediction status_code handling."""
    _ = mock_detector
    detection_interface = Detector(host=TEST_API_URI, port=TEST_API_PORT)
    model_name = detection_interface.available_models[0].name

    # change host to get status_code 422
    detection_interface.host = TEST_API_URI_ERROR

    with pytest.raises(RuntimeError):
        _ = detection_interface.predict(make_images, model_name)
