"""Integration test between model and services."""
import logging
import time
from json import JSONDecodeError
from pathlib import Path

import numpy as np
import pytest
import requests

import core.services as services
from core.model import Video

logger = logging.getLogger(__name__)

TEST_VIDEO = str(
    (
        Path(__file__).parent
        / "test_data"
        / "test-abbor[2021-01-01_00-00-00]-000-small.mp4"
    ).resolve(),
)


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_processing_and_scheduler():
    """Test integration of job processing between API endpoints."""
    response = requests.post(
        "http://127.0.0.1:8000/projects/",
        json={
            "name": "Some name",
            "number": "NINA-123",
            "description": "Some kind of project description",
        },
    )
    assert response.status_code == 201

    project_data = response.json()
    project_id = project_data["id"]

    response_job = requests.post(
        f"http://127.0.0.1:8000/projects/{project_id}/jobs/",
        json={
            "name": "Job name",
            "description": "Job description",
            "location": "test",
            "videos": [TEST_VIDEO],
        },
    )

    assert response_job.status_code == 201

    job_data = response_job.json()
    assert "id" in job_data
    job_id = job_data["id"]

    response = requests.post(
        f"http://127.0.0.1:8000/projects/{project_id}/jobs/{job_id}/start",
    )
    # services.process_job(project_id, job_id)

    url = f"http://127.0.0.1:8000/projects/{project_id}/jobs/{job_id}"
    response_finished = requests.get(url)

    assert response_finished.status_code == 200

    status = ""
    while status != "Done":
        logger.info("Waiting for job to finish.")
        time.sleep(5)
        res = requests.get(url)

        try:
            status = res.json().get("_status", "")
        except JSONDecodeError as e:
            logger.warning(
                f"Response not valid json, error: {repr(e)}, response: {repr(res)}",
            )
            continue

    job_data = requests.get(url).json()
    print(job_data)

    assert job_data["_status"] == "Done"
    assert job_data["progress"] == 100

    assert "stats" in job_data
    assert "labels" in job_data["stats"]
    assert "total_objects" in job_data["stats"]
    assert "total_labels" in job_data["stats"]


def test_video_loader():
    """Tests the video loader utility class."""
    videos = [
        Video.from_path(TEST_VIDEO),
    ]

    video_loader = services.VideoLoader(videos, 15)

    results = []
    for batchnr, (
        progress,
        batch,
        timestamp,
        video_for_frame,
        framenumbers,
    ) in video_loader.generate_batches():
        assert isinstance(batchnr, int)
        assert isinstance(progress, int)
        assert isinstance(batch, np.ndarray)
        assert isinstance(timestamp, list)
        assert isinstance(video_for_frame, dict)
        assert isinstance(framenumbers, list)

        results.append(len(batch))

    assert results[0] == 15  # batch size == 15
    assert results[2] == 15  # Keep using max batch size where it can
    assert results[3] == 5  # Final 5 frames in the 50 frame video
    assert len(results) == 4  # total num batches


def test_video_loader_from_batch():
    """Tests the video loader utility class."""
    videos = [
        Video.from_path(TEST_VIDEO),
    ]

    video_loader = services.VideoLoader(videos, 15)

    results = []
    for batchnr, (_, batch, _, _, _) in video_loader.generate_batches(
        batch_index=1,
    ):
        assert batchnr > 0
        results.append(len(batch))

    assert results[0] == 15  # batch size == 15
    assert results[1] == 15  # Keep using max batch size where it can
    assert results[2] == 5  # Final 5 frames in the 50 frame video
    assert len(results) == 3  # total num batches
