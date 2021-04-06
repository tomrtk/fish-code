"""Unit tests for scheduler."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core import api
from core.model import Job, Project, Status
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers
from core.services import job_queue, populate_queue


@pytest.fixture
def setup_repository():
    """Test repository with empty database.

    Deletes database when run.

    Yields
    ------
    ProjectRepository:
        Empty project repository
    """
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    metadata.drop_all(engine)
    metadata.create_all(engine)
    global sessionfactory
    api.sessionfactory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    start_mappers()

    session = api.sessionfactory()
    proj_repo = ProjectRepository(session)
    job_queue.queue.clear()
    yield proj_repo
    metadata.drop_all(engine)
    clear_mappers()


def test_start_populate_queue(setup_repository: ProjectRepository):
    """Populate queue with two jobs."""
    proj_repo = setup_repository

    proj = Project("tst", "test-abc", "tesst adesc", "silicon valley")

    proj.add_job(Job("heio", "hallaballa", "Cupertino"))
    proj.add_job(Job("asdf", "sadlfslkad", "Cupertino"))
    proj_repo.add(proj)
    proj_repo.save()

    populate_queue()
    assert len(job_queue.queue) == 2


def test_start_populate_queue_empty(setup_repository: ProjectRepository):
    """Populate queue with zero jobs."""
    _ = setup_repository
    populate_queue()
    assert job_queue.empty()


def test_start_populate_queue_done(setup_repository: ProjectRepository):
    """Populate queue with one done and one pending."""
    proj_repo = setup_repository
    proj = Project("tst", "test-abc", "tesst adesc", "silicon valley")

    proj.add_job(Job("heio", "hallaballa", "Cupertino", Status.DONE))
    proj.add_job(Job("asdf", "sadlfslkad", "Cupertino"))
    proj_repo.add(proj)
    proj_repo.save()

    populate_queue()
    assert len(job_queue.queue) == 1


def test_start_populate_exception(setup_repository: ProjectRepository):
    """Testing exceptions in populating."""
    proj_repo = setup_repository

    job_queue.put(Job("heio", "hallaballa", "testloc"))

    with pytest.raises(RuntimeError):
        populate_queue()
