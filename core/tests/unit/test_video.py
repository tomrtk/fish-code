"""Tests for `Video` class."""
import os
from datetime import datetime

import numpy as np
import pytest

import core
from core.model import TimestampNotFoundError, Video, _get_video_metadata


@pytest.fixture
def make_test_video() -> Video:
    """Fixture returning a valid `Video` object."""
    return Video.from_path(
        os.path.dirname(__file__) + "/test-[2020-03-28_12-30-10].mp4"
    )


def test_video_exists(make_test_video):
    """Test `Video.exists()` function."""
    video_valid = make_test_video
    video_invalid = Video(
        "this_does_not_exist", 0, 0, 0, 0, datetime(2020, 3, 28, 10, 20, 30)
    )

    assert video_valid.exists() == True
    assert video_invalid.exists() == False

    video_invalid._path = video_valid._path  # type: ignore
    assert video_invalid.exists() == True


def test_video_members(make_test_video: Video):
    """Test class parameters in class."""
    video = make_test_video
    assert video.frames == 70
    assert video.fps == 25
    assert video.width == 1280
    assert video.height == 720
    assert video.timestamp == datetime(2020, 3, 28, 12, 30, 10)
    assert video.output_height == core.model.VIDEO_DEFAULT_HEIGHT  # type: ignore
    assert video.output_width == core.model.VIDEO_DEFAULT_WIDTH  # type: ignore

    video_raw = Video(
        "/some/path", 8, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )
    assert video_raw.frames == 8


def test_getitem(make_test_video):
    """Test accessing one or more frames."""
    video = make_test_video
    assert video.frames == 70

    frame = video[0]
    assert type(frame) == np.ndarray
    assert frame.ndim == 3

    frames = video[0:-1]
    assert type(frames) == np.ndarray
    assert frames.ndim == 4
    assert frames.shape[0] == 69

    frames = video[0:]
    assert frames.shape[0] == 70

    frames = video[0:-10]
    assert frames.shape[0] == 60


def test_getitem_exceptions(make_test_video):
    """Test exceptions in video class."""
    video = make_test_video
    assert video.frames == 70

    with pytest.raises(IndexError):
        _ = video[70]

    with pytest.raises(IndexError):
        _ = video[-1]

    with pytest.raises(IndexError):
        _ = video[-1:2]

    with pytest.raises(IndexError):
        _ = video[50:70]

    with pytest.raises(NotImplementedError):
        _ = video[0:10:2]

    with pytest.raises(TypeError):
        _ = video["foo"]


def test_make_file_exceptions():
    """Test invalid path and timestamp."""
    with pytest.raises(FileNotFoundError):
        _ = Video.from_path(os.path.dirname(__file__) + "/not_here.mp4")

    with pytest.raises(TimestampNotFoundError):
        _ = Video.from_path(os.path.dirname(__file__) + "/test-no-time.mp4")


def test_timestamp_at(make_test_video: Video):
    """Test video timestamp_at frames."""
    video = make_test_video

    assert video.timestamp_at(0) == datetime(2020, 3, 28, 12, 30, 10)

    assert video.timestamp_at(30) == datetime(2020, 3, 28, 12, 30, 11)

    assert video.timestamp_at(video.frames) == datetime(2020, 3, 28, 12, 30, 12)

    with pytest.raises(IndexError):
        video.timestamp_at(-1)

    with pytest.raises(IndexError):
        video.timestamp_at(video.frames + 1)


def test_video_output_size_default():
    """Test default video output size."""
    video_default = Video.from_path(
        os.path.dirname(__file__) + "/test-[2020-03-28_12-30-10].mp4"
    )

    assert video_default[0].shape[0] == core.model.VIDEO_DEFAULT_HEIGHT  # type: ignore
    assert video_default[0].shape[1] == core.model.VIDEO_DEFAULT_WIDTH  # type: ignore

    assert video_default[0:2].shape[1] == core.model.VIDEO_DEFAULT_HEIGHT  # type: ignore
    assert video_default[0:2].shape[2] == core.model.VIDEO_DEFAULT_WIDTH  # type: ignore


def test_video_output_size_custom():
    """Test default video output custom size."""
    HEIGHT = 720
    WIDTH = 1280

    video_1280 = Video.from_path(
        path=f"{os.path.dirname(__file__)}/test-[2020-03-28_12-30-10].mp4",
        output_width=WIDTH,
        output_height=HEIGHT,
    )

    assert video_1280[0].shape[0] == HEIGHT  # type: ignore
    assert video_1280[0].shape[1] == WIDTH  # type: ignore

    assert video_1280[0:2].shape[1] == HEIGHT
    assert video_1280[0:2].shape[2] == WIDTH

    video_very_small = Video.from_path(
        path=f"{os.path.dirname(__file__)}/test-[2020-03-28_12-30-10].mp4",
        output_width=20,
        output_height=20,
    )

    assert video_very_small[0].shape[0] == 20  # type: ignore
    assert video_very_small[0].shape[1] == 20  # type: ignore


def test_wrong_video_output_size():
    """Test video output size exception, must be positive numbers."""
    with pytest.raises(ValueError):
        _ = Video.from_path(
            path=f"{os.path.dirname(__file__)}/test-[2020-03-28_12-30-10].mp4",
            output_width=-20,
            output_height=20,
        )


def test_get_metadata_exception():
    """Test exception of get metadata function."""
    with pytest.raises(FileNotFoundError):
        _ = _get_video_metadata(os.path.dirname(__file__) + "/not_here.mp4")

    with pytest.raises(RuntimeError):
        _ = _get_video_metadata(os.path.dirname(__file__) + "/abbor.png")


def test_release():
    """Test that check idempotency of `vidcap_release()`."""
    vid = Video.from_path(
        path=f"{os.path.dirname(__file__)}/test-[2020-03-28_12-30-10].mp4",
    )

    try:

        vid.vidcap_release()

        _ = vid[1]

        vid.vidcap_release()
    except:
        assert False
    else:
        assert True


def test_color_channels():
    """Test that color channels are ordered as RGB."""
    vid = Video.from_path(
        path=f"{os.path.dirname(__file__)}/test-[2020-03-28_12-30-10].mp4",
    )

    b = vid[1]  # blue
    g = vid[10]  # green
    r = vid[30]  # red

    check = np.full((b.shape[0], b.shape[1]), 254)

    assert np.allclose(r[:, :, 0], check, atol=5)
    assert np.allclose(g[:, :, 1], check, atol=5)
    assert np.allclose(b[:, :, 2], check, atol=5)


def test_video_iter(make_test_video):
    """Test __iter__ of Video class."""
    video = make_test_video

    it = iter(video)

    frame = next(it)
    assert type(frame) == np.ndarray
    frame = next(it)
    assert type(frame) == np.ndarray

    all_frames = list(it)

    assert len(all_frames) == video.frames
