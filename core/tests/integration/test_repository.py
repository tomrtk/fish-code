"""Integration test between _repository_ and _SQLAlchemy_."""
import pytest

from core import model

# Workaround
from core.repository import SqlAlchemyProjectRepository

# Setup of DB mappings for tests
pytestmark = pytest.mark.usefixtures("mappers")


def test_add_project(sqlite_session_factory):
    """Test project repository class."""
    # Create a db session
    session = sqlite_session_factory()
    # Create a project repository
    repo = SqlAlchemyProjectRepository(session)

    # Create a project to add to repository
    project1 = model.Project("DB test", "ABC-123", "Test prosjekt")
    project2 = model.Project(
        "en til DB test", "ABC-101", "Test prosjekt ABC-101"
    )

    # Add projects into repository
    repo.add(project1)
    repo.add(project2)
    repo.add(project2)

    session.commit()

    # Check that projects in repository is the same as original
    assert repo.get("ABC-123") == project1
    assert repo.get("ABC-101") == project2
    assert repo.list() == [project1, project2]
    assert len(repo) == 2


def test_add_project_with_jobs(sqlite_session_factory):
    """Test project repository class."""
    # Create a db session
    session = sqlite_session_factory()
    # Create a project repository
    repo = SqlAlchemyProjectRepository(session)

    # Create a project to add to repository
    project1 = model.Project("DB test", "ABC-123", "Test prosjekt")
    project1.add_job(model.Job(1, "Project 1: Test job 1"))
    project1.add_job(model.Job(2, "Project 1: Test job 2"))
    project1.add_job(model.Job(3, "Project 1: Test job 3"))
    project2 = model.Project(
        "en til DB test", "ABC-101", "Test prosjekt ABC-101"
    )
    project2.add_job(model.Job(4, "Project 2: Test job 1"))
    project2.add_job(model.Job(5, "Project 2: Test job 2"))
    project2.add_job(model.Job(6, "Project 2: Test job 3"))

    # Add projects into repository
    repo.add(project1)
    repo.add(project2)
    repo.add(project2)

    session.commit()

    # Check that projects in repository is the same as original
    assert repo.get("ABC-123") == project1
    assert repo.get("ABC-101") == project2
    assert repo.list() == [project1, project2]
    assert len(repo) == 2
