"""Integration tests for web `ui`."""
import logging
from pathlib import Path
import time
import os

import flask
import pytest
import requests

import ui
from ui.main import create_app

logger = logging.getLogger(__name__)

TEST_VIDEO_PATH = (
    (
        Path(__file__).parent
        / "test_data"
        / "test-abbor[2021-01-01_00-00-00]-000-small.mp4"
    )
    .resolve()
    .as_posix()
)

WAIT_TIME = 30 if os.getenv("GITHUB_ACTIONS") == "true" else 5


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
def test_post_new_project_and_job() -> None:
    """Test making a new project and job, end to end test."""
    app = create_app()
    ui.projects.projects.ROOT_FOLDER = "/"

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
        response = _new_job(
            client,
            1,
            "ui test job name",
            "ui test job location",
            "ui test job description",
            [f"{str(TEST_VIDEO_PATH)}"],
        )

        assert response.status_code == 200
        assert b"ui test job name" in response.data
        assert b"ui test job location" in response.data
        assert b"ui test job description" in response.data

        # toggle job
        response = client.put(
            "/projects/1/jobs/1/toggle",
            follow_redirects=True,
        )
        assert response.status_code == 201
        assert (
            response.data == b'{"new_status":"queued","old_status":"pending"}\n'
        )

        # wait for job to complete
        host_core = app.config.get("BACKEND_URL")
        url = f"{host_core}/projects/1/jobs/1"

        while requests.get(url).json()["_status"] != "Done":
            logger.info("Waiting for job to finish.")
            time.sleep(WAIT_TIME)

        # wait due to CI need some more time to complete job
        time.sleep(WAIT_TIME)

        # test object preview
        response = client.get(
            "/projects/objects/0/preview",
            follow_redirects=True,
        )
        assert response.status_code == 422
        assert b"Object id 0 not valid." in response.data

        response = client.get(
            "/projects/objects/1/preview",
        )
        assert response.status_code == 302
        assert response.headers["Location"] == f"{host_core}/objects/1/preview"

        # test download csv ok
        response = client.get(
            "/projects/1/jobs/1/csv",
            follow_redirects=True,
        )
        assert response.status_code == 200

        # test download csv not ok
        response = _new_job(
            client,
            1,
            "ui test job name",
            "ui test job location",
            "ui test job description",
            [f"{str(TEST_VIDEO_PATH)}"],
        )
        assert response.status_code == 200

        response = client.get(
            "/projects/1/jobs/2/csv",
            follow_redirects=True,
        )
        assert response.status_code == 404

        response = client.get(
            "/projects/1/jobs/0/csv",
            follow_redirects=True,
        )
        assert response.status_code == 404


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_get_objects_from_job_errors() -> None:
    """Test errors in route for objects pagination in `ui`."""
    app = create_app()

    with app.test_client() as client:
        response = client.post(
            "/projects/1/jobs/1/objects",
            data={"draw": 1, "start": 0, "length": 10},
            follow_redirects=True,
        )
        assert response.status_code == 500

        response = client.post(
            "/projects/1/jobs/0/objects",
            data={"draw": 1, "start": 0, "length": 10},
            follow_redirects=True,
        )
        assert response.status_code == 422
        assert b"Invalid project or job id." in response.data


@pytest.mark.usefixtures("start_core", "detection_api", "tracing_api")
def test_errorhandler_404() -> None:
    """Test 404 errorhandler."""
    app = create_app()

    with app.test_client() as client:
        response = client.post(
            "/jobs",
            data={"draw": 1, "start": 0, "length": 10},
            follow_redirects=True,
        )

        assert response.status_code == 404
        assert b"Something fishy happened..." in response.data
        assert b"Nothing was found here." in response.data
        assert b"404 Not Found" in response.data
