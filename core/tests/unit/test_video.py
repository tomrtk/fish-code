from datetime import datetime

import numpy as np
import pytest

from core.model import Video


@pytest.fixture
def make_test_video() -> Video:
    return Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")


def test_video_exists(make_test_video):
    video_valid = make_test_video
    video_invalid = Video("this_does_not_exist", 0, 0, 0, 0)

    assert video_valid.exists() == True
    assert video_invalid.exists() == False

    video_invalid._path = video_valid._path
    assert video_invalid.exists() == True


def test_video_members(make_test_video: Video):
    video = make_test_video
    assert video.frames == 70
    assert video.fps == 25
    assert video.width == 1280
    assert video.height == 720
    assert video.timestamp == datetime(2020, 3, 28, 12, 30, 10)

    video_raw = Video("/some/path", 8, 25, 512, 512)
    assert video_raw.frames == 8


def test_getitem(make_test_video):
    video = make_test_video
    assert video.frames == 70

    frame = video[0]
    assert type(frame) == np.ndarray
    assert frame.ndim == 3

    frames = video[0:70]
    assert type(frames) == np.ndarray
    assert frames.ndim == 4
    assert frames.shape[0] == 70


def test_getitem_exceptions(make_test_video):
    video = make_test_video
    assert video.frames == 70

    with pytest.raises(IndexError) as excinfo:
        _ = video[70]

    with pytest.raises(IndexError) as excinfo:
        _ = video[-1]

    with pytest.raises(NotImplementedError) as excinfo:
        _ = video[0:10:2]


def test_timestamp_at(make_test_video: Video):
    video = make_test_video

    assert video.timestamp_at(0) == datetime(2020, 3, 28, 12, 30, 10)

    assert video.timestamp_at(30) == datetime(2020, 3, 28, 12, 30, 11)

    assert video.timestamp_at(video.frames) == datetime(2020, 3, 28, 12, 30, 12)

    with pytest.raises(IndexError):
        video.timestamp_at(-1)

    with pytest.raises(IndexError):
        video.timestamp_at(video.frames + 1)
