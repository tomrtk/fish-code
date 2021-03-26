"""Tests the job class functionality."""
from datetime import timedelta

import pytest

from core.model import Job, JobStatusException, Object, Status, Video


@pytest.fixture
def make_test_job() -> Job:
    """Create a test job with some objects."""
    job = Job("Test Name", "Test Description", "Test location")
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


def test_add_video(make_test_job):
    """Test adding a video to the job."""
    job = make_test_job
    vid1 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    assert job.videos == []
    assert job.add_video(vid1) == True
    assert job.videos == [vid1]
    assert job.add_video(vid1) == False
    assert job.videos == [vid1]


def test_add_list_videos(make_test_job):
    """Test adding videos to the job with a list."""
    job = make_test_job
    vid1 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    vid2 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    vid3 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")

    vid2.timestamp = vid1.timestamp + timedelta(minutes=30)
    vid3.timestamp = vid2.timestamp + timedelta(minutes=30)

    assert job.add_videos([vid3, vid1, vid2]) == True
    assert job.videos == [vid1, vid2, vid3]
    assert job.add_videos([vid3, vid2]) == False
    assert job.videos == [vid1, vid2, vid3]


def test_remove_video(make_test_job):
    """Test removing a video from the job."""
    job = make_test_job
    vid1 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    job.add_video(vid1)
    assert job.videos == [vid1]
    assert job.remove_video(vid1) == True
    assert job.videos == []
    assert job.remove_video(vid1) == False


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
    """Test getting result objects from the job."""
    job = make_test_job

    results = job.get_result()

    assert len(results) == 4

    assert "track_id" in results[0]
    assert "label" in results[0]
    assert "probability" in results[0]
    assert "time_in" in results[0]
    assert "time_out" in results[0]
