"""Tests for API."""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker
from starlette.responses import Response

from core import model
from core.api import core, make_db, schema
from core.api.api import get_runtime_repo
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers


def test_pydantic_schema():  # noqa: D103
    job = schema.Job(
        id=1,
        name="Test",
        description="Testing",
        _status=model.Status.PENDING,
    )

    jobs = set()
    jobs.add(job)
    jobs.add(job)
    assert len(jobs) == 1


def test_production_make_db():
    """Test production FastAPI dependency `make_db`."""
    core.dependency_overrides[make_db] = make_db
    core.dependency_overrides[get_runtime_repo] = get_runtime_repo
    with TestClient(core) as client:
        response = client.get("/projects/")

        assert response.status_code == 200
    core.dependency_overrides[make_db] = make_test_db
    core.dependency_overrides[get_runtime_repo] = get_test_repo


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


def get_test_repo(session=Depends(make_test_db)):
    sessionRepo = ProjectRepository(session)

    proj = model.Project("test", "test", "test")
    job = model.Job("Test Name", "Test Description", status=model.Status.DONE)
    obj1 = model.Object(1)
    obj1.add_detection(model.Detection(model.BBox(10, 20, 30, 40), 0.7, 1, 1))
    obj1.add_detection(model.Detection(model.BBox(15, 25, 35, 45), 0.6, 1, 2))
    obj1.add_detection(model.Detection(model.BBox(20, 30, 40, 50), 0.7, 2, 3))
    obj1.track_id = 1
    job.add_object(obj1)

    obj2 = model.Object(2)
    obj2.add_detection(model.Detection(model.BBox(40, 50, 60, 70), 0.7, 2, 2))
    obj2.add_detection(model.Detection(model.BBox(45, 55, 65, 75), 0.6, 2, 3))
    obj2.add_detection(model.Detection(model.BBox(50, 60, 70, 100), 0.7, 1, 4))
    obj2.track_id = 2
    job.add_object(obj2)

    proj = proj.add_job(job)
    sessionRepo.add(proj)
    sessionRepo.save()

    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


# Override what database to use for tests
core.dependency_overrides[make_db] = make_test_db
core.dependency_overrides[get_runtime_repo] = get_test_repo


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
            "jobs": [],
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
            "jobs": [],
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
            "jobs": [],
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
            "_objects": [],
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
                "_objects": [],
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
            "jobs": [],
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
            "_objects": [],
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
            "id": project_id,
            "name": "Project name",
            "number": "AB-123",
            "description": "A project description",
            "location": None,
            "jobs": [],
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
            "_objects": [],
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
            "_objects": [],
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
            "_objects": [],
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
            "_objects": [],
        }
