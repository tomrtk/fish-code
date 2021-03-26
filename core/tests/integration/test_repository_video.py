from datetime import datetime

import pytest

from core import model
from core.repository.video import SqlAlchemyVideoRepository

pytestmark = pytest.mark.usefixtures("mappers")


@pytest.fixture
def make_test_video() -> model.Video:
    return model.Video.from_path("./tests/unit/test.mp4")


def test_add_object(sqlite_session_factory):
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
    assert repo.get(1).frames == vid1.frames
    assert repo.list() == [vid1, vid2]
    assert len(repo.list()) == 2


def test_change_object(sqlite_session_factory):
    session = sqlite_session_factory()

    repo = SqlAlchemyVideoRepository(session)

    obj1 = model.Video(
        "/some/path", 20, 25, 512, 512, datetime(2020, 3, 28, 10, 20, 30)
    )
    repo.add(obj1)
    repo.save()

    obj_change = repo.get(1)
    assert obj_change.frames == 20

    obj_change.frames = 50
    repo.save()
    assert repo.get(1).frames == 50


def test_remove_object(sqlite_session_factory):
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
