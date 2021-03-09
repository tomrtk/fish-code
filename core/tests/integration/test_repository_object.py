import pytest

from core import model
from core.repository.object import SqlAlchemyObjectRepository

pytestmark = pytest.mark.usefixtures("mappers")


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
