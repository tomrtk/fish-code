import pytest

from core.model import Job, Project


@pytest.fixture
def make_test_project() -> Project:
    project = Project("Test name", "Test description")
    project.add_job(Job("Test job name 1"))
    project.add_job(Job("Test job name 2"))
    project.add_job(Job("Test job name 3"))
    return project


def test_make_project_and_add_job(make_test_project):
    project = make_test_project
    project.add_job(Job("Test job name 1"))
    project.add_job(Job("This test is new"))

    assert project.number_of_jobs == 4


def test_make_project_get_jobs(make_test_project):
    project = make_test_project
    jobs = project.get_jobs()

    assert isinstance(jobs, list)
    assert isinstance(jobs[0], Job)


def test_remove_job(make_test_project):
    project = make_test_project
    jobs = project.get_jobs()

    assert project.remove_job(jobs[1]) == True
    assert len(project.get_jobs()) == 2
    assert project.remove_job(jobs[1]) == False
    assert len(project.get_jobs()) == 2

    project.add_job(jobs[1])

    assert len(project.get_jobs()) == 3
