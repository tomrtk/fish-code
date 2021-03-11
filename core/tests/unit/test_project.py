import pytest

from core.model import Job, Project, Status


@pytest.fixture
def make_test_project() -> Project:
    project = Project("Test name", "NINA-123", "Test description")
    project.add_job(Job("Test job name 1", "Test description 1"))
    project.add_job(Job("Test job name 2", "Test description 2"))
    project.add_job(Job("Test job name 3", "Test description 3"))
    return project


def test_make_project_and_add_job(make_test_project):
    project = make_test_project
    project.add_job(Job("Test job name 1", "Test description 1"))
    project.add_job(Job("This test is new", "Test description 2"))

    assert project.number_of_jobs == 4


def test_make_project_get_jobs(make_test_project):
    project = make_test_project
    jobs = project.get_jobs()

    assert isinstance(jobs, list)
    assert isinstance(jobs[0], Job)


def test_get_job(make_test_project):
    project = make_test_project

    new_job = Job("New Job", "New Job Desc")
    new_job.id = 1

    project.add_job(new_job)

    valid_job = project.get_job(1)
    assert valid_job.name == "New Job"

    missing_job = project.get_job(13)
    assert missing_job == None


def test_remove_job(make_test_project):
    project = make_test_project
    jobs = project.get_jobs()

    assert project.remove_job(jobs[1]) == True
    assert len(project.get_jobs()) == 2
    assert project.remove_job(jobs[1]) == False
    assert len(project.get_jobs()) == 2

    project.add_job(jobs[1])

    assert len(project.get_jobs()) == 3


def test_status_job():
    job = Job("test", "test description")

    assert job.status() == Status.PENDING
    job.start()
    assert job.status() == Status.RUNNING
    job.pause()
    assert job.status() == Status.PAUSED
    job.complete()
    assert job.status() == Status.DONE
