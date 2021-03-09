import pytest

from core import model
from core.repository.object import SqlAlchemyObjectRepository

pytestmark = pytest.mark.usefixtures("mappers")


@pytest.fixture
def make_test_obj() -> model.Object:
    obj = model.Object(1)
    obj.add_detection(model.Detection(model.BBox(*[10, 20, 30, 40]), 1.0, 1, 1))
    obj.add_detection(model.Detection(model.BBox(*[15, 25, 35, 45]), 0.8, 2, 2))
    obj.add_detection(model.Detection(model.BBox(*[20, 30, 40, 50]), 0.1, 1, 3))
    obj.add_detection(model.Detection(model.BBox(*[25, 35, 45, 55]), 0.5, 1, 4))

    return obj


def test_add_object(sqlite_session_factory):
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = model.Object(1)
    obj2 = model.Object(2)

    repo.add(obj1)
    repo.add(obj2)

    repo.save()

    assert repo.get(1) == obj1
    assert repo.get(2) == obj2
    assert repo.list() == [obj1, obj2]
    assert len(repo.list()) == 2


def test_change_object(sqlite_session_factory):
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = model.Object(1)
    repo.add(obj1)
    repo.save()

    obj_change = repo.get(1)
    assert obj_change.label == 1

    obj_change.label = 2
    repo.save()
    assert repo.get(1).label == 2


def test_remove_object(sqlite_session_factory):
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = model.Object(1)
    repo.add(obj1)
    repo.save()

    assert len(repo.list()) == 1

    obj_del = repo.get(1)

    if obj_del:
        repo.remove(obj_del)
    repo.save()

    assert len(repo.list()) == 0


def test_add_full_object(sqlite_session_factory, make_test_obj: model.Object):
    session = sqlite_session_factory()
    repo = SqlAlchemyObjectRepository(session)

    obj = make_test_obj

    repo.add(obj)
    repo.save()
    assert (len(repo.list())) == 1

    obj_get = repo.get(1)

    assert (
        obj_get._detections[1].score == obj._detections[1].score
        and obj_get._detections[2].frame == obj._detections[2].frame
    )
