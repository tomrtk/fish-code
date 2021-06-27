"""Unit testing ui Flask app and api Client."""
from dataclasses import asdict

import pytest

from ui.main import create_app
from ui.projects.api import Client
from ui.projects.model import ProjectBare

TEST_API_URI = "mock://testing"


@pytest.fixture
def get_app():
    """Create flask app with test config."""
    return create_app({"BACKEND_URL": TEST_API_URI})


@pytest.fixture
def mock_client(requests_mock):
    """Mock response from core api to unit test ui."""
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


def test_client_get_project(mock_client):
    """Unit test the Client."""
    client = Client(TEST_API_URI)

    response = client.get_project(1)
    assert response is not None
    assert isinstance(response, ProjectBare)
    assert response.name == "Test name"


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
