"""Integration test between _repository_ and _SQLAlchemy_."""
from typing import List

import pytest

from core import model
from core.repository import SqlAlchemyProjectRepository


def test_add_project(sqlite_session_factory):
    """Test project repository class."""
    # Create a db session
    session = sqlite_session_factory()
    # Create a project repository
    repo = SqlAlchemyProjectRepository(session)

    # Create a project to add to repository
    project1 = model.Project("DB test", "NINA-123", "Test prosjekt")
    project2 = model.Project(
        "en til DB test", "NINA-124", "Test prosjekt ABC-101", "Some location"
    )

    # Add projects into repository
    repo.add(project1)
    repo.add(project2)
    repo.add(project2)

    session.commit()

    # Check that projects in repository is the same as original
    assert repo.get(1) == project1
    assert repo.get(2) == project2
    assert repo.list() == [project1, project2]
    assert repo.get(2).location == "Some location"
    assert len(repo) == 2


def test_add_project_with_jobs(sqlite_session_factory):
    """Test project repository class."""
    # Create a db session
    session = sqlite_session_factory()
    # Create a project repository
    repo = SqlAlchemyProjectRepository(session)

    # Create a project to add to repository
    project1 = model.Project("DB test", "NINA-123", "Test prosjekt")
    project1.add_job(
        model.Job(
            "Project 1: Test job 1", "Test description 1", "Test location"
        )
    )
    project1.add_job(
        model.Job(
            "Project 1: Test job 2", "Test description 2", "Test location"
        )
    )
    project1.add_job(
        model.Job(
            "Project 1: Test job 3", "Test description 3", "Test location"
        )
    )
    project2 = model.Project(
        "en til DB test", "NINA-124", "Test prosjekt ABC-101"
    )
    project2.add_job(
        model.Job(
            "Project 2: Test job 1", "Test description 1", "Test location"
        )
    )
    project2.add_job(
        model.Job(
            "Project 2: Test job 2", "Test description 2", "Test location"
        )
    )
    project2.add_job(
        model.Job(
            "Project 2: Test job 3", "Test description 3", "Test location"
        )
    )

    # Add projects into repository
    repo.add(project1)
    repo.add(project2)
    repo.add(project2)

    session.commit()

    # Check that projects in repository is the same as original
    assert repo.get(1) == project1
    assert repo.get(2) == project2
    assert repo.list() == [project1, project2]
    assert len(repo) == 2


def test_add_project_with_location(sqlite_session_factory):
    """Test that location gets saved to the database."""
    session1 = sqlite_session_factory()
    repo1 = SqlAlchemyProjectRepository(session1)

    # Create a project to add to repository
    projectA = model.Project("aaa", "bbb", "ccc", "ddd")
    projectB = model.Project("111", "222", "333")

    # Add projects into repository
    repo1.add(projectA)
    repo1.add(projectB)
    repo1.save()

    session2 = sqlite_session_factory()
    repo2 = SqlAlchemyProjectRepository(session2)

    assert repo2.get(1).location == "ddd"
    assert repo2.get(2).location is None

    repo2.get(2).location = "444"
    repo2.save()

    assert repo2.get(2).location == "444"


def test_save_project(sqlite_session_factory):
    """Tests saving the project to disk, and retrieving it afterwards."""
    # Create a db session
    session1 = sqlite_session_factory()
    # Create a project repository
    repo1 = SqlAlchemyProjectRepository(session1)

    project1 = model.Project("DB test", "NINA-123", "Test prosjekt")
    project1.add_job(
        model.Job(
            "Project 1: Test job 1", "Test description 1", "Test location"
        )
    )
    project1.add_job(
        model.Job(
            "Project 1: Test job 2", "Test description 2", "Test location"
        )
    )

    repo1.add(project1)
    project_get = repo1.get(1)

    assert project_get != None

    project_get.description = "Changed description"
    repo1.save()
    session1.close()

    session2 = sqlite_session_factory()
    repo2 = SqlAlchemyProjectRepository(session2)

    project_after = repo2.get(1)
    assert project_after != None
    assert project_after.description == "Changed description"
    assert hex(id(project_get)) != hex(id(project_after))


def test_add_job_with_objects(
    sqlite_session_factory, make_test_obj: List[model.Object]
):
    """Test adding a job with attached objects."""
    session1 = sqlite_session_factory()
    repo1 = SqlAlchemyProjectRepository(session1)
    project1 = model.Project("DB test", "NINA-123", "Test prosjekt")
    job1 = model.Job("DB test", "Description", "Test location")

    job1.add_object(make_test_obj[0])
    job1.add_object(make_test_obj[1])
    assert job1.number_of_objects() == 2

    project1.add_job(job1)
    repo1.add(project1)
    project_get = repo1.get(1)
    assert project_get is not None
    assert project_get.get_jobs()[0].number_of_objects() == 2

    repo1.save()
    session1.close()

    session2 = sqlite_session_factory()
    repo2 = SqlAlchemyProjectRepository(session2)
    project_get2 = repo2.get(1)
    assert project_get2 is not None
    assert project_get2.get_jobs()[0].number_of_objects() == 2


def test_regression_add_jobs_with_same_name(sqlite_session_factory):
    """Test regression of not able to add two jobs with same name to project.

    issue #88.
    """
    session = sqlite_session_factory()
    repo = SqlAlchemyProjectRepository(session)
    project = model.Project(
        "Project name", "NINA-123", "Test prosjekt description"
    )
    repo.add(project)
    repo.save()

    job1 = model.Job("Job test", "Description", "Location")
    job2 = model.Job("Job test", "Description", "Location")

    repo_project = repo.get(1)
    repo_project.add_job(job1)
    repo.save()

    repo_project = repo.get(1)
    repo_project.add_job(job2)
    repo.save()

    assert len(repo.get(1).get_jobs()) == 2
