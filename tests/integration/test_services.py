"""Integration test between model and services."""
import logging

import pytest
import time
import core.services as services

from core.model import Project, Job, Video
import requests

logger = logging.getLogger(__name__)


def test_scheduler():
    """Test the processing of a job."""
    project = Project("Project name", "NINA-123", "Project description")
    project.id = 50000
    job = Job("Test Name", "Test Description", "Test Location")
    job.id = 50000
    project.add_job(job)
    vid1 = Video.from_path(
        "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
    )
    job.add_videos([vid1])
    job.start()

    # Check that the scheduling thread starts and queue
    services.start_scheduler()
    assert services.schedule_thread.is_alive()
    assert services.job_queue.qsize() == 0

    # Insert job to scheduler
    services.queue_job(project.id, job.id)
    assert services.job_queue.qsize() == 1

    # Check that the job gets consumed
    time.sleep(1)
    assert services.job_queue.qsize() == 0

    # Ensure scheduler stops
    services.stop_scheduler()
    time.sleep(1)
    assert not services.schedule_thread.is_alive()


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_processing():
    """Test integration of job processing between API endpoints."""
    response = requests.post(
        "http://127.0.0.1:8000/projects/",
        json={
            "name": "Some name",
            "number": "NINA-123",
            "description": "Some kind of project description",
        },
    )
    assert response.status_code == 200

    project_data = response.json()
    project_id = project_data["id"]

    response_job = requests.post(
        f"http://127.0.0.1:8000/projects/{project_id}/jobs/",
        json={
            "name": "Job name",
            "description": "Job description",
            "location": "test",
            "videos": [
                "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
            ],
        },
    )

    assert response_job.status_code == 201

    job_data = response_job.json()
    assert "id" in job_data
    job_id = job_data["id"]

    services.process_job(project_id, job_id)

    response_finished = requests.get(
        f"http://127.0.0.1:8000/projects/{project_id}/jobs/{job_id}"
    )
    assert response_finished.status_code == 200
    job_data = response_finished.json()

    objects = job_data["_objects"]
    assert len(objects) == 1  # Only one fish should be detected

    obj = objects[0]
    assert obj["label"] == 4  # Abbor
    assert obj["time_in"] == "2021-01-01T00:00:00"
    assert obj["time_out"] == "2021-01-01T00:00:01"

    logger.info(f"Test results from processing job {job_id}: {obj}")


def test_video_loader():
    """Tests the video loader utility class."""
    videos = [
        Video.from_path(
            "./tests/integration/test_data/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
        ),
    ]

    video_loader = services.VideoLoader(videos, 15)

    results = []
    for batch, _ in video_loader:
        results.append(len(batch))

    assert results[0] == 15  # batch size == 15
    assert results[2] == 15  # Keep using max batch size where it can
    assert results[3] == 5  # Final 5 frames in the 50 frame video
    assert len(results) == 4  # total num batches
