import pytest

from core.model import Job, Object


@pytest.fixture
def make_test_job() -> Job:
    job = Job("Test Name", "Test Description")
    job.add_object(Object(1))
    job.add_object(Object(2))
    job.add_object(Object(3))
    job.add_object(Object(3))

    return job


def test_add_object(make_test_job: Job):
    job = make_test_job
    assert job.number_of_objects() == 4

    job.add_object(Object(1))
    assert job.number_of_objects() == 5


def test_get_object(make_test_job: Job):
    job = make_test_job

    obj = job.get_object(1)

    assert obj.label == 2

    assert job.get_object(10) == None
