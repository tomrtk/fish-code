"""Tests the job class functionality."""
import pytest

from core.model import Job, JobStatusException, Object, Status


@pytest.fixture
def make_test_job() -> Job:
    """Create a test job with some objects."""
    job = Job("Test Name", "Test Description")
    job.add_object(Object(1))
    job.add_object(Object(2))
    job.add_object(Object(3))
    job.add_object(Object(3))

    return job


def test_add_object(make_test_job: Job):
    """Test adding object to the job."""
    job = make_test_job
    assert job.number_of_objects() == 4

    job.add_object(Object(1))
    assert job.number_of_objects() == 5


def test_get_object(make_test_job: Job):
    """Retrieves object from a job."""
    job = make_test_job

    obj = job.get_object(1)

    assert obj.label == 2

    assert job.get_object(10) == None


def test_job_status(make_test_job: Job):
    """Test logic regarding job status and setting of the statuses."""
    job = make_test_job

    assert job.status() == Status.PENDING

    # This should not work
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    assert job.status() == Status.PENDING

    # start job
    job.start()
    assert job.status() == Status.RUNNING

    # Cannot start a started job
    with pytest.raises(JobStatusException):
        job.start()
    assert job.status() == Status.RUNNING

    # Pause job
    job.pause()
    assert job.status() == Status.PAUSED

    # This should not work
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    assert job.status() == Status.PAUSED

    # Restart job
    job.start()
    assert job.status() == Status.RUNNING

    # Complete job
    job.complete()
    assert job.status() == Status.DONE

    # This should not work
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    with pytest.raises(JobStatusException):
        job.start()
    assert job.status() == Status.DONE


def test_get_result(make_test_job: Job):
    job = make_test_job

    results = job.get_result()

    assert len(results) == 4

    assert "track_id" in results[0]
    assert "label" in results[0]
    assert "probability" in results[0]
    assert "time_in" in results[0]
    assert "time_out" in results[0]
