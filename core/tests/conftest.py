"""Defining pytest fixtures used during testing."""
import os
from datetime import datetime
from typing import List

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

import core.model as model
from core.repository.orm import metadata, start_mappers


@pytest.fixture
def in_memory_sqlite_db():
    """Create a sqlite database in memory for use with tests."""
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    yield engine
    metadata.drop_all(engine)


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):
    """Create a SQLAlchemy Session to be used during testing."""
    yield sessionmaker(bind=in_memory_sqlite_db)


@pytest.fixture
def mappers():
    """Map the objects to DB tables start of test and clean up after."""
    clear_mappers()
    start_mappers()
    yield
    # Cleanup after test
    clear_mappers()


@pytest.fixture
def make_test_obj() -> List[model.Object]:
    """Make two fully fledged test objects."""
    obj1 = model.Object(1)
    obj1._detections = []
    obj1.id = 1
    obj1.add_detection(
        model.Detection(model.BBox(10, 20, 30, 40), 1.0, 1, 1, 1, 1)
    )
    obj1.add_detection(
        model.Detection(model.BBox(15, 25, 35, 45), 0.8, 2, 2, 2, 1)
    )
    obj1.add_detection(
        model.Detection(model.BBox(20, 30, 40, 50), 0.1, 1, 3, 3, 1)
    )
    obj1.add_detection(
        model.Detection(model.BBox(25, 35, 45, 55), 0.5, 1, 4, 4, 1)
    )
    obj1.time_in = datetime(2020, 3, 28, 10, 20, 30)
    obj1.time_out = datetime(2020, 3, 28, 10, 40, 30)
    obj1.track_id = 1

    obj2 = model.Object(2)
    obj2.id = 2
    obj2._detections = []
    obj2.add_detection(
        model.Detection(model.BBox(10, 20, 30, 40), 1.0, 1, 1, 1, 1)
    )
    obj2.add_detection(
        model.Detection(model.BBox(15, 25, 35, 45), 0.8, 2, 2, 2, 1)
    )
    obj2.add_detection(
        model.Detection(model.BBox(20, 30, 40, 50), 0.1, 1, 3, 3, 1)
    )
    obj2.add_detection(
        model.Detection(model.BBox(25, 35, 45, 55), 0.5, 1, 4, 4, 1)
    )
    obj2.time_in = datetime(2020, 3, 28, 11, 20, 30)
    obj2.time_out = datetime(2020, 3, 28, 11, 40, 30)
    obj2.track_id = 2

    return [obj1, obj2]


@pytest.fixture(autouse=True)
def cleanup():
    """Remove databases after tests are done.

    Rename `data.db` if found in `core` for the duration of the test, to
    avoid removing a `data.db` from manual testing of `core`.

    Note: is set to `autouse`, this fixture is implicit run for each test
    in `core`.
    """
    if os.path.exists("data.db"):
        os.rename("data.db", "data.db.bak")

    try:
        yield
    finally:
        # remove data.db made during test.
        if os.path.exists("data.db"):
            os.remove("data.db")

        if os.path.exists("data.db.bak"):
            os.rename("data.db.bak", "data.db")
