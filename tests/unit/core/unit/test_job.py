"""Tests the job class functionality."""
from datetime import timedelta
from pathlib import Path

import pytest

from core import model
from core.model import (
    Detection,
    Job,
    JobStatusException,
    Object,
    Status,
    TimestampNotFoundError,
    Video,
)

TEST_VIDEO = str(
    (Path(__file__).parent / "test-[2020-03-28_12-30-10].mp4").resolve()
)
TEST_VIDEO_NO_TIME = str(Path(__file__).parent / "test-no-time.mp4")


@pytest.fixture()
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

    assert obj is not None

    assert obj.label == 2

    assert job.get_object(10) is None


def test_add_video(make_test_job):
    """Test adding a video to the job."""
    job = make_test_job
    vid1 = Video.from_path(TEST_VIDEO)
    assert job.videos == []
    assert job.add_video(vid1) is True
    assert job.videos == [vid1]
    assert job.add_video(vid1) is False
    assert job.videos == [vid1]


def test_add_list_videos(make_test_job):
    """Test adding videos to the job with a list."""
    job = make_test_job
    vid1 = Video.from_path(TEST_VIDEO)
    vid2 = Video.from_path(TEST_VIDEO)
    vid3 = Video.from_path(TEST_VIDEO)

    assert job.add_videos([vid1, vid3, vid2]) is False
    assert job.videos == []

    vid2.timestamp = vid1.timestamp + timedelta(minutes=30)
    vid3.timestamp = vid2.timestamp + timedelta(minutes=30)

    assert job.add_videos([vid3, vid1, vid2]) is True
    assert job.videos == [vid1, vid2, vid3]
    assert job.add_videos([vid3, vid2]) is False
    assert job.videos == [vid1, vid2, vid3]


def test_remove_video(make_test_job):
    """Test removing a video from the job."""
    job = make_test_job
    vid1 = Video.from_path(TEST_VIDEO)
    job.add_video(vid1)
    assert job.videos == [vid1]
    assert job.remove_video(vid1) is True
    assert job.videos == []
    assert job.remove_video(vid1) is False


def test_job_status(make_test_job: Job):
    """Test logic regarding job status and setting of the statuses."""
    job = make_test_job

    assert job.status() == Status.PENDING

    # This should not work
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    with pytest.raises(JobStatusException):
        job.mark_as_error()
    assert job.status() == Status.PENDING

    # queue job
    job.queue()
    assert job.status() == Status.QUEUED

    # Cannot queue a queued job
    with pytest.raises(JobStatusException):
        job.queue()
    with pytest.raises(JobStatusException):
        job.complete()
    with pytest.raises(JobStatusException):
        job.mark_as_error()
    assert job.status() == Status.QUEUED

    # start job
    job.start()
    assert job.status() == Status.RUNNING

    # Cannot start a started job
    with pytest.raises(JobStatusException):
        job.start()
    with pytest.raises(JobStatusException):
        job.queue()
    assert job.status() == Status.RUNNING

    # Pause job
    job.pause()
    assert job.status() == Status.PAUSED

    # This should not work
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    with pytest.raises(JobStatusException):
        job.mark_as_error()
    assert job.status() == Status.PAUSED

    # Restart job
    job.start()
    assert job.status() == Status.RUNNING

    # Mark status as error
    job.mark_as_error()
    assert job.status() == Status.ERROR

    # Change job status to running for remaining tests
    job._status = Status.RUNNING
    assert job.status() == Status.RUNNING

    # Complete job
    job.complete()
    assert job.status() == Status.DONE

    # This should not work
    with pytest.raises(JobStatusException):
        job.queue()
    with pytest.raises(JobStatusException):
        job.pause()
    with pytest.raises(JobStatusException):
        job.complete()
    with pytest.raises(JobStatusException):
        job.start()
    with pytest.raises(JobStatusException):
        job.mark_as_error()
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


def test_job_hash(make_test_job: Job):
    """Test job __hash__ by use of a set()."""
    job = make_test_job
    job_set = set()

    job_set.add(job)
    job_set.add(job)

    assert len(job_set) == 1


def test_job_eq():
    """Test job __eq__."""
    job1 = Job("Test job 1", "Tester", "Test")
    job2 = Job("Test job 1", "Tester", "Test")
    job1.id = 1
    job2.id = 1

    assert job1 == job2

    job2.id = 2
    assert job1 != job2
    assert job1 != "test"


def test_repr():
    """Test job __repr__ function."""
    job = Job("Test job 1", "Tester", "Test")

    assert (
        repr(job)
        == "<class 'core.model.Job'>: {'id': None, 'name': 'Test job 1', "
        + "'description': 'Tester', '_status': <Status.PENDING: 'Pending'>, "
        + "'_objects': [], 'videos': [], 'location': 'Test', 'next_batch': 0, "
        + "'progress': 0}"
    )


def test_job_add_video(make_test_job):
    """Test adding video to a job."""
    job = make_test_job

    with pytest.raises(TimestampNotFoundError):
        _ = job.add_video(Video.from_path(TEST_VIDEO_NO_TIME))

    # The video will never be without a timestamp, but we try break it here
    # to check return value of add_video on a job
    video = Video(TEST_VIDEO_NO_TIME, 1, 1, 1, 1, None, 1, 1)
    assert job.add_video(video) is False


def test_job_total_frames(make_test_job):
    """Test calculating frames in job."""
    job = make_test_job
    ret = job.add_video(Video.from_path(TEST_VIDEO))
    assert ret is True

    assert job.total_frames() == 70


def test_job_stats_empty():
    """Testing job stats with zero results."""
    job = Job("name", "desc", "testland")

    stats_empty = {
        "total_objects": 0,
        "total_labels": 0,
        "labels": {},
    }
    assert job.stats == stats_empty


def test_job_stats_full():
    """Test job stats with results."""
    job = Job("name", "desc", "testland")

    job.add_object(
        Object(
            1,
            [
                Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 1),
                Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 2),
                Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 3),
            ],
        )
    )
    job.add_object(
        Object(
            2,
            [
                Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 1),
                Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 2),
                Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 3),
            ],
        )
    )
    job.add_object(
        Object(
            2,
            [
                Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 3),
                Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 4),
                Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 5),
            ],
        )
    )

    stats_full = {
        "total_objects": 3,
        "total_labels": 2,
        "labels": {
            1: 1,
            2: 2,
        },
    }

    assert job.stats == stats_full
