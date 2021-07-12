"""Unit testing ui Flask app and api Client."""
from dataclasses import asdict

import pytest
import requests

from ui.main import create_app
from ui.projects.api import Client
from ui.projects.model import ProjectBare, Object

TEST_API_URI = "mock://testing"
TEST_API_URI_ERROR = "mock://testingerrors"


@pytest.fixture
def get_app():
    """Create flask app with test config."""
    return create_app({"BACKEND_URL": TEST_API_URI})


@pytest.fixture
def mock_client(requests_mock):
    """Mock response from core api to unit test ui."""
    requests_mock.real_http = True  # type: ignore
    # Creation of objects needed for reply from core:
    header = {
        "x-total": "1",
        "x-page": "1",
        "x-per-page": "1",
        "x-total-pages": "1",
        "x-prev-page": "1",
        "x-next-page": "1",
    }
    project = ProjectBare(
        1, "Test name", "location", "this is a project", "NINA-123", 0
    )
    projects = [
        asdict(project),
    ]
    objects = {
        "total_objects": 1,
        "data": [
            {
                "id": 1,
                "label": "Abbor",
                "probability": 0.9640775752067566,
                "_detections": {
                    "Abbor": [
                        0.9656107425689697,
                        0.9656107425689697,
                        0.9641051292419434,
                        0.9641051292419434,
                    ]
                },
                "time_in": "2021-01-01T00:00:00",
                "time_out": "2021-01-01T00:00:01",
                "video_ids": [1],
            }
        ],
    }
    job = {
        "name": "string",
        "description": "string",
        "location": "string",
        "id": 1,
        "_status": "Pending",
        "_objects": [],
        "videos": [],
        "progress": 0,
    }
    job_done = {
        "name": "string",
        "description": "string",
        "location": "string",
        "id": 2,
        "_status": "Done",
        "_objects": [],
        "videos": [],
        "progress": 100,
    }

    # mock for Client.get_projects() call to core api
    requests_mock.get(
        f"{TEST_API_URI}/projects/", headers=header, json=projects
    )

    # mock for Client.check_api()
    requests_mock.get(f"{TEST_API_URI}/")

    # mock for Client.get_project
    requests_mock.get(
        f"{TEST_API_URI}/projects/1", headers=header, json=asdict(project)
    )

    # mock Client.get_objects
    requests_mock.get(f"{TEST_API_URI}/projects/1/jobs/1/objects", json=objects)
    requests_mock.get(f"{TEST_API_URI}/projects/1/jobs/2/objects", json=objects)
    requests_mock.get(
        f"{TEST_API_URI_ERROR}/projects/1/jobs/1/objects",
        exc=requests.ConnectionError,
    )
    requests_mock.get(
        f"{TEST_API_URI_ERROR}/projects/1/jobs/0/objects",
        status_code=422,
    )

    # mock Client.get_job
    requests_mock.get(f"{TEST_API_URI}/projects/1/jobs/1", json=job)
    requests_mock.get(f"{TEST_API_URI}/projects/1/jobs/2", json=job_done)

    # mock core object preview endpoint
    requests_mock.get(f"{TEST_API_URI}/objects/1/preview", json={})

    return requests_mock


def test_client_get_projects(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_projects()
    assert response is not None

    projects, x_total = response
    assert len(projects) == 1
    assert isinstance(projects[0], ProjectBare)
    assert projects[0].name == "Test name"
    assert x_total == 1


def test_client_get_project(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_project(1)
    assert response is not None
    assert isinstance(response, ProjectBare)
    assert response.name == "Test name"


def test_client_get_objects(mock_client) -> None:
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_objects(1, 1, 0, 10)
    assert response is not None
    objects, count = response[0], response[1]
    assert isinstance(objects, list)
    assert isinstance(objects[0], Object)
    assert count == 1
    assert objects[0].label == "Abbor"


def test_client_get_objects_no_response() -> None:
    """Unit test the Client to get object when no connection to api."""
    client = Client("http://test")

    response = client.get_objects(1, 1, 0, 10)
    assert response is None


# Testing of the Flask app can be more or less be copied from integration
# tests in root.
def test_projects(mock_client, get_app):
    """Test projects listing in ui."""
    app = get_app

    with app.test_client() as client:
        response = client.get("/projects", follow_redirects=True)

        assert response.status_code == 200
        assert b"Test name" in response.data
        assert b"NINA-123" in response.data


def test_pending_job_and_objects(mock_client, get_app) -> None:
    """Test job page with objects."""
    app = get_app

    with app.test_client() as client:
        response = client.get("/projects/1/jobs/1", follow_redirects=True)

        assert response.status_code == 200
        assert b"Test name" in response.data
        assert b"Statistics" in response.data
        assert (
            b"Not enough information gathered to display statistics."
            in response.data
        )


def test_done_job_and_objects(mock_client, get_app) -> None:
    """Test job page with objects."""
    app = get_app

    with app.test_client() as client:
        response = client.get("/projects/1/jobs/2", follow_redirects=True)

        assert response.status_code == 200
        assert b"Test name" in response.data
        assert b"Statistics" in response.data
        assert b"Total" in response.data
        assert b"Counter" in response.data


def test_get_objects_from_job_route(mock_client, get_app) -> None:
    """Test route for pagination in `ui`."""
    app = get_app

    with app.test_client() as client:
        response = client.post(
            "/projects/1/jobs/1/objects",
            data={"draw": 1, "start": 0, "length": 10},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"data" in response.data
        assert b"draw" in response.data
        assert b"recordsTotal" in response.data
        assert b"recordsFiltered" in response.data


def test_get_objects_from_job_errors(mock_client, get_app) -> None:
    """Test errors in route for objects pagination in `ui`."""
    app = create_app({"BACKEND_URL": TEST_API_URI_ERROR})

    with app.test_client() as client:
        response = client.post(
            "/projects/1/jobs/1/objects",
            data={"draw": 1, "start": 0, "length": 10},
            follow_redirects=True,
        )
        assert response.status_code == 500


def test_errorhandler_404(get_app) -> None:
    """Test 404 errorhandler."""
    app = get_app

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


def test_get_object_preview(mock_client, get_app) -> None:
    """Test errors in route for object preview."""
    app = get_app

    with app.test_client() as client:
        response = client.get(
            "/projects/objects/1/preview",
        )
        assert response.status_code == 302

        response = client.get(
            "/projects/objects/0/preview",
        )
        assert response.status_code == 422
