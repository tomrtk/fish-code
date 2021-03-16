"""Tests for API."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core import model
from core.api import core, make_db, schema
from core.repository.orm import metadata, start_mappers


def test_pydantic_schema():  # noqa: D103
    job = schema.Job(
        id=1, name="Test", description="Testing", _status=model.Status.PENDING
    )

    jobs = set()
    jobs.add(job)
    jobs.add(job)
    assert len(jobs) == 1


def test_production_make_db():
    """Test production FastAPI dependency `make_db`."""
    core.dependency_overrides[make_db] = make_db
    with TestClient(core) as client:
        response = client.get("/projects/")

        assert response.status_code == 200
    core.dependency_overrides[make_db] = make_test_db


def make_test_db():
    """Override dependency for FastAPI."""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()
    try:
        yield session()
    finally:
        clear_mappers()


# Override what database to use for tests
core.dependency_overrides[make_db] = make_test_db


def test_get_projects():
    """Test getting project list endpoint."""
    with TestClient(core) as client:
        response = client.get("/projects/")

        assert response.status_code == 200


def test_add_project():
    """Test posting a new project."""
    with TestClient(core) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 200
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response = response.json()
        assert response == {
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
            "description": "A project description",
            "location": None,
        }


def test_add_project_with_location():
    """Test posting a new project with location string."""
    with TestClient(core) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
                "location": "Testing",
            },
        )
        assert response.status_code == 200
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response = response.json()
        assert response == {
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
            "description": "A project description",
            "location": "Testing",
        }


def test_get_project():
    """Test retrieving a single project."""
    with TestClient(core) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response_post_project.status_code == 200

        project_data = response_post_project.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response_get_project = client.get(f"/projects/{project_id}")
        assert response_get_project.json() == {
            "description": "A project description",
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
            "location": None,
        }

        response_wrong_project = client.get("/projects/999999")
        assert response_wrong_project.status_code == 404


def test_add_and_get_job():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(core) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 200
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )

        assert response_job.status_code == 200

        job_data = response_job.json()
        assert "id" in job_data
        job_id = job_data["id"]
        response_job_json = response_job.json()
        assert response_job_json == {
            "name": "Job name",
            "description": "Job description",
            "id": job_id,
            "_status": "Pending",
        }

        response = client.get(f"/projects/{project_id}/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert len(jobs) == 1
        assert jobs == [
            {
                "name": "Job name",
                "description": "Job description",
                "id": job_id,
                "_status": "Pending",
            }
        ]


def test_get_job():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(core) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response_post_project.status_code == 200

        project_data = response_post_project.json()
        assert "id" in project_data

        project_id = project_data["id"]

        response_get_project = client.get(f"/projects/{project_id}")
        assert response_get_project.json() == {
            "id": project_id,
            "description": "A project description",
            "name": "Project name",
            "number": "AB-123",
            "location": None,
        }

        response_post_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )
        assert response_post_job.status_code == 200

        job_data = response_post_job.json()
        assert "id" in job_data

        job_id = job_data["id"]

        response_get_job = client.get(f"/projects/{project_id}/jobs/{job_id}")
        assert response_get_job.status_code == 200

        assert response_get_job.json() == {
            "description": "Job description",
            "id": job_id,
            "name": "Job name",
            "_status": "Pending",
        }

        response = client.get(f"/projects/999999/jobs/{job_id}")
        assert response.status_code == 404

        response = client.get(f"/projects/{project_id}/jobs/99999")
        assert response.status_code == 404


def test_project_not_existing():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(core) as client:

        response = client.get(f"/projects/0/jobs")
        assert response.status_code == 404

        response = client.get(f"/projects/abc/jobs")
        assert response.status_code == 422

        response = client.post(
            "/projects/-1/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )
        assert response.status_code == 404


def test_set_job_status():
    """Test updating the status of jobs."""
    with TestClient(core) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response_post_project.status_code == 200

        project_data = response_post_project.json()
        assert "id" in project_data

        project_id = project_data["id"]

        response_get_project = client.get(f"/projects/{project_id}")
        assert response_get_project.json() == {
            "description": "A project description",
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
        }

        response_post_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={"name": "Job name", "description": "Job description"},
        )
        assert response_post_job.status_code == 200

        job_data = response_post_job.json()
        assert "id" in job_data

        job_id = job_data["id"]

        response_get_job = client.get(f"/projects/{project_id}/jobs/{job_id}")
        assert response_get_job.status_code == 200

        # Check that status is initially "Pending"
        assert response_get_job.json() == {
            "description": "Job description",
            "id": job_id,
            "name": "Job name",
            "_status": "Pending",
        }

        # Start job and check its started
        response_post_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/start",
        )
        assert response_post_job.status_code == 200
        assert response_post_job.json() == {
            "description": "Job description",
            "id": job_id,
            "name": "Job name",
            "_status": "Running",
        }

        # Should not be able to start a started job
        response_post_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/start",
        )
        assert response_post_job.status_code == 403

        # Pause job and check status
        response_post_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/pause",
        )
        assert response_post_job.status_code == 200
        assert response_post_job.json() == {
            "description": "Job description",
            "id": job_id,
            "name": "Job name",
            "_status": "Paused",
        }

        # Should not be able to pause a paused job
        response_post_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/pause",
        )
        assert response_post_job.status_code == 403

        # Should be able to restart a paused job
        response_post_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/start",
        )
        assert response_post_job.status_code == 200
        assert response_post_job.json() == {
            "description": "Job description",
            "id": job_id,
            "name": "Job name",
            "_status": "Running",
        }
