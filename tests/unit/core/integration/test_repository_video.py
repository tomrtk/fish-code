"""Integrations tests for Video Repository."""
from datetime import datetime

import pytest

from core import model
from core.repository.video import SqlAlchemyVideoRepository


@pytest.fixture()
def make_test_video() -> model.Video:
    """Make test video."""
    return model.Video.from_path("./tests/unit/test.mp4")


def test_add_object(sqlite_session_factory):
    """Test add object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyVideoRepository(session)

    vid1 = model.Video(
        "/some/path", 30, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )
    vid2 = model.Video(
        "/some/other/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )

    repo.add(vid1)
    repo.add(vid2)

    repo.save()

    assert repo.get(1)._path == vid1._path
    assert repo.get(1).frame_count == vid1.frame_count
    assert repo.list() == [vid1, vid2]
    assert len(repo.list()) == 2


def test_change_object(sqlite_session_factory):
    """Test change object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyVideoRepository(session)

    obj1 = model.Video(
        "/some/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )
    repo.add(obj1)
    repo.save()

    obj_change = repo.get(1)
    assert obj_change.frame_count == 20

    obj_change.frame_count = 50
    repo.save()
    assert repo.get(1).frame_count == 50


def test_remove_object(sqlite_session_factory):
    """Test remove object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyVideoRepository(session)

    vid = model.Video(
        "/some/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )
    repo.add(vid)
    repo.save()

    assert len(repo.list()) == 1

    obj_del = repo.get(1)

    if obj_del:
        repo.remove(obj_del)
    repo.save()

    assert len(repo.list()) == 0


def test_add_video_with_frame(sqlite_session_factory):
    """Tests adding a video with some frames."""
    session = sqlite_session_factory()
    repo = SqlAlchemyVideoRepository(session)

    vid = model.Video(
        "/some/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )

    frame = model.Frame(
        10,
        [model.Detection(model.BBox(11, 22, 33, 44), 0.9, 2, 9, 1, 1)],
    )

    vid.add_detection_frame(frame)
    repo.add(vid)
    repo.save()

    session = sqlite_session_factory()
    repo = SqlAlchemyVideoRepository(session)

    vid_ret = repo.get(1)
    assert len(vid_ret.frames) == 1
    frame_ret = vid_ret.frames[0]

    assert len(frame_ret.detections) == 1
    detection_ret = frame_ret.detections[0]

    assert detection_ret.bbox == model.BBox(11, 22, 33, 44)
    assert detection_ret.probability == 0.9
    assert detection_ret.label == 2
    assert detection_ret.frame == 9


def test_video_with_frame_exceptions(sqlite_session_factory):
    """Test exceptions with videos that have frames."""
    session = sqlite_session_factory()
    repo = SqlAlchemyVideoRepository(session)

    vid = model.Video(
        "/some/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )

    repo.add(vid)

    frame = model.Frame(
        10,
        [],
    )

    frame_big = model.Frame(
        10000,
        [],
    )

    with pytest.raises(IndexError):
        vid.add_detection_frame(frame_big)

    vid.add_detection_frame(frame)
    repo.save()

    with pytest.raises(RuntimeError):
        vid.add_detection_frame(frame)
