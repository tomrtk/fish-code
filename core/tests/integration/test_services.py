"""Integration test between model and services."""
import logging
from datetime import timedelta

import pytest

from core.model import Job, Video
from core.services import process_job

logger = logging.getLogger(__name__)


def test_job_processing():
    """Test the processing of a job."""
    job = Job("Test Name", "Test Description")
    vid1 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    vid2 = Video.from_path("./tests/unit/test-[2020-03-28_12-30-10].mp4")
    vid2.timestamp = vid1.timestamp + timedelta(minutes=30)
    job.add_videos([vid1, vid2])
    job.start()
    process_job(job)
