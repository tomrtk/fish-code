from typing import List

import pytest

from core import model
from core.repository.object import SqlAlchemyObjectRepository

pytestmark = pytest.mark.usefixtures("mappers", "make_test_obj")


def test_add_object(sqlite_session_factory, make_test_obj: List[model.Object]):
    """Test adding of object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = make_test_obj[0]

    repo.add(obj1)

    repo.save()

    assert repo.get(1) == obj1
    assert repo.list() == [obj1]
    assert len(repo.list()) == 1


def test_change_object(
    sqlite_session_factory, make_test_obj: List[model.Object]
):
    """Tests updating of object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = make_test_obj[0]
    repo.add(obj1)
    repo.save()

    obj_change = repo.get(1)
    assert obj_change.label == 1

    obj_change.label = 2
    repo.save()
    assert repo.get(1).label == 2


def test_remove_object(
    sqlite_session_factory, make_test_obj: List[model.Object]
):
    """Tests removing of object."""
    session = sqlite_session_factory()

    repo = SqlAlchemyObjectRepository(session)

    obj1 = make_test_obj[0]
    repo.add(obj1)
    repo.save()

    assert len(repo.list()) == 1

    obj_del = repo.get(1)

    if obj_del:
        repo.remove(obj_del)
    repo.save()

    assert len(repo.list()) == 0


def test_add_full_object(
    sqlite_session_factory, make_test_obj: List[model.Object]
):
    """Tests adding full a object."""
    session = sqlite_session_factory()
    repo = SqlAlchemyObjectRepository(session)

    obj = make_test_obj[0]

    repo.add(obj)
    repo.save()
    assert (len(repo.list())) == 1

    obj_get = repo.get(1)

    assert (
        obj_get._detections[1].probability == obj._detections[1].probability
        and obj_get._detections[2].frame == obj._detections[2].frame
    )
