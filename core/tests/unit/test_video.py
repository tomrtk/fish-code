import pytest

from core.model import Video


@pytest.fixture
def make_test_video() -> Video:
    return Video.from_path("./tests/unit/test.mp4")


def test_video_exists(make_test_video):
    video_valid = make_test_video
    video_invalid = Video("this_does_not_exist", 0)

    assert video_valid.exists() == True
    assert video_invalid.exists() == False

    video_invalid._path = video_valid._path
    assert video_invalid.exists() == True


def test_num_frames(make_test_video):
    video = make_test_video
    assert video.frames == 70

    video_raw = Video("/some/path", 8)
    assert video_raw.frames == 8
