"""Defining pytest fixtures used during testing."""
from datetime import datetime
from pathlib import Path

import pytest

import core.main
import core.model as model
from core.repository.project import SqlAlchemyProjectRepository as ProjectRepo
from core.repository.orm import metadata

TEST_VIDEO: str = str(
    (
        Path(__file__).parent
        / "integration"
        / "test-abbor[2021-01-01_00-00-00]-000-small.mp4"
    ).resolve()
)


@pytest.fixture(scope="function")
def in_memory_sqlite_db():
    """Create a sqlite database in memory for use with tests."""
    core.main.setup(db_name=":memory:")
    yield core.main.engine
    metadata.drop_all(core.main.engine)
    core.main.shutdown()
    core.main.sessionfactory = None
    core.main.engine = None


@pytest.fixture(scope="function")
def sqlite_session_factory(in_memory_sqlite_db):
    """Create a SQLAlchemy Session to be used during testing."""
    yield core.main.sessionfactory


@pytest.fixture
def make_test_obj() -> list[model.Object]:
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


@pytest.fixture(scope="function")
def make_test_project_repo(sqlite_session_factory) -> ProjectRepo:
    """Create a test project for testing."""
    project_repo = ProjectRepo(sqlite_session_factory())

    project = model.Project(
        "Test name", "NINA-123", "Test description", "Test location"
    )
    job = model.Job("Test job name 1", "Test description 1", "Test location")
    job._status = model.Status.DONE

    for i in range(1000):
        obj = model.Object(i)
        obj._detections = []
        obj.add_detection(
            model.Detection(model.BBox(10, 20, 30, 40), 1.0, 1, 1, 1, 1)
        )
        obj.add_detection(
            model.Detection(model.BBox(15, 25, 35, 45), 0.8, 2, 2, 2, 1)
        )
        obj.time_in = datetime(2020, 3, 28, 10, 20, 30)
        obj.time_out = datetime(2020, 3, 28, 10, 40, 30)
        obj.track_id = i
        job.add_object(obj)

    project.add_job(job)

    job_2 = model.Job("Test job name 2", "Test description 2", "Test location")
    job_2._status = model.Status.QUEUED
    project.add_job(job_2)

    job_3 = model.Job("Test job name 3", "Test description 3", "Test location")
    job_3._status = model.Status.RUNNING
    project.add_job(job_3)

    job_4 = model.Job("Test job name 4", "Test description 4", "Test location")
    job_4.add_video(model.Video.from_path(TEST_VIDEO))
    job_4._status = model.Status.QUEUED
    project.add_job(job_4)

    project_repo.add(project)
    project_repo.save()

    return project_repo
