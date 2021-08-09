"""Unit testing ui Flask app and api Client."""
import base64
import json
from dataclasses import asdict
from http import HTTPStatus
from os import chmod
from unittest.mock import patch

import pytest
import requests
from werkzeug.exceptions import HTTPException

from ui.main import create_app
from ui.projects.api import Client
from ui.projects.model import Job, Object, ProjectBare

TEST_API_URI = "mock://testing"
TEST_API_URI_ERROR = "mock://testingerrors"


@pytest.fixture
def test_client():
    """Create flask app with test config."""
    app = create_app({"BACKEND_URL": TEST_API_URI, "TESTING": True})

    with app.test_client() as client:
        yield client


@pytest.fixture
def test_client_error():
    """Create flask app with test config."""
    app = create_app({"BACKEND_URL": TEST_API_URI_ERROR, "TESTING": True})

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_client(
    requests_mock,
):
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
        "videos": [],
        "progress": 0,
        "stats": {
            "total_objects": 0,
            "total_labels": 0,
            "labels": {},
        },
    }
    job_done = {
        "name": "string",
        "description": "string",
        "location": "string",
        "id": 2,
        "_status": "Done",
        "videos": [],
        "progress": 100,
        "stats": {
            "total_objects": 1,
            "total_labels": 1,
            "labels": {
                "Abbor": 1,
            },
        },
    }

    root = [
        {
            "id": "/mnt/videos",
            "text": "/mnt/videos",
            "children": [
                {
                    "id": "/mnt/videos/summer-2021",
                    "text": "summer-2021",
                    "children": True,
                },
                {
                    "id": "/mnt/videos/summer-2020",
                    "text": "summer-2020",
                    "type": "file",
                },
            ],
            "type": "root",
        }
    ]

    child = [
        {
            "id": "/mnt/videos/summer-2021",
            "text": "summer-2021",
            "children": [
                {"id": 4, "text": "Child node 3"},
                {"id": 5, "text": "Child node 4"},
            ],
        }
    ]

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

    # mock Client.get_job - broken
    requests_mock.get(
        f"{TEST_API_URI}/projects/13", json={}, status_code=HTTPStatus.NOT_FOUND
    )
    requests_mock.get(
        f"{TEST_API_URI}/projects/1/jobs/31",
        json={},
        status_code=HTTPStatus.NOT_FOUND,
    )
    requests_mock.get(
        f"{TEST_API_URI}/projects/13/jobs/31",
        json={},
        status_code=HTTPStatus.NOT_FOUND,
    )

    # mock core object preview endpoint
    requests_mock.get(f"{TEST_API_URI}/objects/1/preview", json={})

    # mock storage
    requests_mock.get(f"{TEST_API_URI}/storage/bad_parameter")
    requests_mock.get(f"{TEST_API_URI}/storage", json=root)
    requests_mock.get(f"{TEST_API_URI}/storage/Lw==", json=root)
    requests_mock.get(f"{TEST_API_URI}/projects/storage/Lw==", json=root)
    requests_mock.get(
        f"{TEST_API_URI}/storage/L21udC9zdW1tZXItMjAyMQ==", json=child
    )

    # permissionerror
    # Mock with no path is mocked inside the function
    requests_mock.get(
        f"{TEST_API_URI}/storage/cGVybWlzc2lvbmVycm9y",
        status_code=HTTPStatus.FORBIDDEN,
    )

    # mock ...

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


@patch("os.access", return_value=False)
def test_client_get_storage(mock, mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response_root = client.get_storage()
    assert response_root is not None
    assert "children" in response_root[0]

    response_child = client.get_storage("/mnt/summer-2021")
    assert response_child is not None
    assert "children" in response_child[0]
    assert response_child[0].get("text") == "summer-2021"

    # Overwrite the global mock.
    mock_client.get(
        f"{TEST_API_URI}/storage",
        status_code=HTTPStatus.FORBIDDEN,
    )

    with pytest.raises(PermissionError):
        _ = client.get_storage()

    with pytest.raises(PermissionError):
        _ = client.get_storage("permissionerror")


def test_client_get_project(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_project(1)
    assert response is not None
    assert isinstance(response, ProjectBare)
    assert response.name == "Test name"


def test_client_get_job(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_job(1, 1)
    assert response is not None
    assert isinstance(response, Job)
    assert response.name == "string"


def test_client_get_noexisting_job(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_job(1, 31)
    assert response is None

    response = client.get_job(13, 31)
    assert response is None


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
def test_projects(mock_client, test_client):
    """Test projects listing in ui."""
    response = test_client.get("/projects", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test name" in response.data
    assert b"NINA-123" in response.data


def test_pending_job_and_objects(mock_client, test_client) -> None:
    """Test job page with objects."""
    response = test_client.get("/projects/1/jobs/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test name" in response.data
    assert b"Statistics" in response.data
    assert (
        b"Not enough information gathered to display statistics."
        in response.data
    )


def test_done_job_and_objects(mock_client, test_client) -> None:
    """Test job page with objects."""
    response = test_client.get("/projects/1/jobs/2", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test name" in response.data
    assert b"Statistics" in response.data
    assert b"Total" in response.data
    assert b"Counter" in response.data


def test_get_objects_from_job_route(mock_client, test_client) -> None:
    """Test route for pagination in `ui`."""
    response = test_client.post(
        "/projects/1/jobs/1/objects",
        data={"draw": 1, "start": 0, "length": 10},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"data" in response.data
    assert b"draw" in response.data
    assert b"recordsTotal" in response.data
    assert b"recordsFiltered" in response.data


def test_get_objects_from_job_errors(mock_client, test_client_error) -> None:
    """Test errors in route for objects pagination in `ui`."""
    response = test_client_error.post(
        "/projects/1/jobs/1/objects",
        data={"draw": 1, "start": 0, "length": 10},
        follow_redirects=True,
    )
    assert response.status_code == 500


def test_errorhandler_404(test_client) -> None:
    """Test 404 errorhandler."""
    response = test_client.post(
        "/jobs",
        data={"draw": 1, "start": 0, "length": 10},
        follow_redirects=True,
    )
    assert response.status_code == 404
    assert b"Something fishy happened..." in response.data
    assert b"Nothing was found here." in response.data
    assert b"404 Not Found" in response.data


def test_get_object_preview(mock_client, test_client) -> None:
    """Test errors in route for object preview."""
    response = test_client.get(
        "/projects/objects/1/preview",
    )
    assert response.status_code == 302

    response = test_client.get(
        "/projects/objects/0/preview",
    )
    assert response.status_code == 422


def test_get_storage_endpoint(mock_client, test_client) -> None:
    """Test route for getting storage."""
    response = test_client.get("/projects/storage/bad_parameter")
    assert response.status_code == 400

    response = test_client.get("/projects/storage")
    assert response.status_code == 200
    assert response is not None
    assert b"children" in response.data

    response = test_client.get("/projects/storage/Lw==")
    assert response.status_code == 200
    assert response is not None
    assert b"children" in response.data

    response = test_client.get("/projects/storage/L21udC9zdW1tZXItMjAyMQ==")
    assert response.status_code == 200
    assert response is not None
    assert b"children" in response.data
    data = json.loads(response.data)
    assert data[0]["text"] == "summer-2021"


def test_get_storage_endpoint_permission_denied(
    mock_client,
    test_client,
) -> None:
    """Test for PermissionError."""
    mock_client.get(f"{TEST_API_URI}/storage", status_code=403)
    response = test_client.get(
        f"/projects/storage",
    )
    assert response.status_code == 403

    response = test_client.get(
        f"/projects/storage/cGVybWlzc2lvbmVycm9y",
    )
    assert response.status_code == 403
