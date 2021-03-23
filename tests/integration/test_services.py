"""Integration test between model and services."""
import logging

import pytest
from core.services import process_job, VideoLoader

from core.model import Job, Video, Status
from core.services import process_job
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("tracing_api", "detection_api")
def test_job_processing():
    """Test the processing of a job."""
    job = Job("Test Name", "Test Description")
    vid1 = Video.from_path(
        "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
    )
    job.add_videos([vid1])
    job.start()
    finished_job = process_job(job)
    print(finished_job._objects)
    assert len(finished_job._objects) > 0
    for o in finished_job._objects:
        assert isinstance(o.time_in, datetime)
        assert isinstance(o.time_out, datetime)
        assert o.time_in <= o.time_out
    assert finished_job.status() == Status.DONE


def test_video_loader():
    """Tests the video loader utility class."""
    videos = [
        Video.from_path(
            "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
        ),
    ]

    video_loader = VideoLoader(videos, 10)

    results = []
    for batch, _ in video_loader:
        results.append(len(batch))

    assert results[0] == 10  # batch size == 10
    assert len(results) == 5  # total num batches
