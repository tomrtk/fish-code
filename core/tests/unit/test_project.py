"""Tests the project class functionality."""
import pytest

from core.model import Job, Project


@pytest.fixture
def make_test_project() -> Project:
    """Create a test project for testing."""
    project = Project(
        "Test name", "NINA-123", "Test description", "Test location"
    )
    project.add_job(Job("Test job name 1", "Test description 1"))
    project.add_job(Job("Test job name 2", "Test description 2"))
    project.add_job(Job("Test job name 3", "Test description 3"))
    return project


def test_project_location(make_test_project):
    """Test optional location string in constructor."""
    project = make_test_project
    assert project.location == "Test location"
    project = Project("Test name", "123", "Desc")
    assert project.location == None


def test_make_project_and_add_job(make_test_project):
    """Tests creation of a project, and adding of jobs to it."""
    project = make_test_project
    project.add_job(Job("This test is new", "Test description 2"))

    assert project.number_of_jobs == 4


def test_make_project_get_jobs(make_test_project):
    """Tests creating a project, and retrieving all jobs from it."""
    project = make_test_project
    jobs = project.get_jobs()

    assert isinstance(jobs, list)
    assert isinstance(jobs[0], Job)


def test_get_job(make_test_project):
    """Test getting a single job from a project by id."""
    project = make_test_project

    new_job = Job("New Job", "New Job Desc")
    new_job.id = 1

    project.add_job(new_job)

    valid_job = project.get_job(1)
    assert valid_job.name == "New Job"

    missing_job = project.get_job(13)
    assert missing_job == None


def test_remove_job(make_test_project):
    """Test removing a job from the project by id."""
    project = make_test_project
    jobs = project.get_jobs().copy()

    assert project.remove_job(jobs[1]) == True
    assert len(project.get_jobs()) == 2
    assert project.remove_job(jobs[1]) == False
    assert len(project.get_jobs()) == 2

    project.add_job(jobs[1])

    assert len(project.get_jobs()) == 3
