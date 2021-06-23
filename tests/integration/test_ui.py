"""Integration tests for web `ui`."""
import logging
from pathlib import Path

import pytest

from ui.main import create_app

logger = logging.getLogger(__name__)

TEST_VIDEO_PATH = (
    Path(__file__).parent
    / "test_data"
    / "test-abbor[2021-01-01_00-00-00]-000.mp4"
).resolve()


def test_index():
    """Test main index page of ui.

    Do not depend on any of the backends to be running.
    """
    app = create_app()

    with app.test_client() as client:
        response = client.get("/")

        assert response.status_code == 200
        assert b"Projects" in response.data


def test_api_down():
    """Test api is down check."""
    app = create_app()

    with app.test_client() as client:
        response = client.get("/projects", follow_redirects=True)

        assert response.status_code == 502
        assert b"API Is Down" in response.data

        response = client.get("/projects/new", follow_redirects=True)

        assert response.status_code == 502
        assert b"API Is Down" in response.data


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_projects():
    """Test main index page of ui."""
    app = create_app()

    with app.test_client() as client:
        response = client.get("/projects", follow_redirects=True)

        assert response.status_code == 200
        assert b"New Project" in response.data
        assert b"Projects" in response.data


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_new_project_page_content():
    """Test main index page of ui."""
    app = create_app()

    with app.test_client() as client:
        response = client.get("/projects/new", follow_redirects=True)

        assert response.status_code == 200
        assert b"New Project" in response.data
        assert b"Name" in response.data
        assert b"Number (ID)" in response.data
        assert b"Location" in response.data
        assert b"Description" in response.data
        assert b"Cancel" in response.data
        assert b"Create" in response.data


def _new_project(client, name, number, location, description):
    """Post new project."""
    return client.post(
        "/projects/new",
        data={
            "project_name": name,
            "project_id": number,
            "project_location": location,
            "project_desc": description,
        },
        follow_redirects=True,
    )


def _new_job(client, project_id, name, location, description, video):
    """Post new job to project."""
    return client.post(
        f"/projects/{project_id}/jobs/new",
        data={
            "job_name": name,
            "job_location": location,
            "job_description": description,
            "tree_data": video,
        },
        follow_redirects=True,
    )


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_post_new_project_and_job():
    """Test making a new project and job."""
    app = create_app()

    with app.test_client() as client:
        response = _new_project(
            client,
            "ui project test name",
            "ui project no 123",
            "ui project test location",
            "ui project test desc",
        )

        assert response.status_code == 200
        assert b"ui project test name" in response.data
        assert b"ui project no 123" in response.data
        assert b"ui project test loc" in response.data
        assert b"ui project test desc" in response.data

    # test content of new job page
    with app.test_client() as client:
        response = client.get("/projects/1/jobs/new", follow_redirects=True)

        assert response.status_code == 200
        assert b"New Job" in response.data
        assert b"Name" in response.data
        assert b"Location" in response.data
        assert b"Description" in response.data
        assert b"Choose Files" in response.data
        assert b"Cancel" in response.data
        assert b"Create" in response.data

    # test posting a new job
    with app.test_client() as client:
        response = _new_job(
            client,
            1,
            "ui test job name",
            "ui test job location",
            "ui test job description",
            [str(TEST_VIDEO_PATH)],
        )

        assert response.status_code == 200
        assert b"ui test job name" in response.data
        assert b"ui test job location" in response.data
        assert b"ui test job description" in response.data
