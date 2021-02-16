from core.model import Job, Project


def test_make_project_and_add_job():
    project = Project("Test name", "Test project number", "Test description")
    project.add_job(Job("Test job name 1"))
    project.add_job(Job("Test job name 1"))
    project.add_job(Job("Test job name 2"))
    project.add_job(Job("Test job name 3"))

    assert project.number_of_jobs == 3
