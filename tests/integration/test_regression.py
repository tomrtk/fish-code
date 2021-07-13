"""Regression tests for bug fixes, needing the full stack running."""
import logging
import time
from pathlib import Path

import requests
import pytest

logger = logging.getLogger(__name__)

TEST_VIDEO = str(
    (
        Path(__file__).parent
        / "test_data"
        / "test-abbor-small[2021-01-02_00-00-00]-000.mp4"
    ).resolve()
)


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_regression_add_two_jobs_with_objects() -> None:
    """Test regression of objects from previous job shows up.

    Ref. github issue #81
    """
    response = requests.post(
        "http://127.0.0.1:8000/projects/",
        json={
            "name": "Some name",
            "number": "NINA-123",
            "description": "Some kind of project description",
        },
    )
    assert response.status_code == 201

    response_job = requests.post(
        "http://127.0.0.1:8000/projects/1/jobs/",
        json={
            "name": "Job 1",
            "description": "Job description",
            "location": "test",
            "videos": [TEST_VIDEO],
        },
    )

    assert response_job.status_code == 201
    response = requests.post(
        "http://127.0.0.1:8000/projects/1/jobs/1/start",
    )

    url = "http://127.0.0.1:8000/projects/1/jobs/1"
    while requests.get(url).json()["_status"] != "Done":
        logger.info("Waiting for job to finish.")
        time.sleep(5)

    response_job = requests.post(
        "http://127.0.0.1:8000/projects/1/jobs/",
        json={
            "name": "Job 2",
            "description": "Job description",
            "location": "test",
            "videos": [TEST_VIDEO],
        },
    )

    assert response_job.status_code == 201
    response = requests.post(
        "http://127.0.0.1:8000/projects/1/jobs/2/start",
    )

    url = "http://127.0.0.1:8000/projects/1/jobs/2"

    while requests.get(url).json()["_status"] != "Done":
        logger.info("Waiting for job to finish.")
        time.sleep(5)

    job1 = requests.get(
        "http://127.0.0.1:8000/projects/1/jobs/1",
    ).json()
    job2 = requests.get(
        "http://127.0.0.1:8000/projects/1/jobs/2",
    ).json()

    assert job1["stats"]["total_objects"] == 1
    assert job2["stats"]["total_objects"] == 1  # bug results this to be 2
