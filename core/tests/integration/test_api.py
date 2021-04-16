"""Tests for API."""
from datetime import datetime

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker
from sqlalchemy.orm.session import close_all_sessions

import core
from core import api, model

# from core.api import core_api, schema, get_runtime_repo, sessionfactory
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers


def test_pydantic_schema():  # noqa: D103
    job = api.schema.Job(
        id=1,
        name="Test",
        description="Testing",
        _status=model.Status.PENDING,
        location="Test",
    )

    jobs = set()
    jobs.add(job)
    jobs.add(job)
    assert len(jobs) == 1


def test_production_make_db():
    """Test production FastAPI dependency `make_db`."""
    api.core_api.dependency_overrides[
        api.get_runtime_repo
    ] = api.get_runtime_repo
    with TestClient(api.core_api) as client:
        response = client.get("/projects/")

        assert response.status_code == 200
    api.core_api.dependency_overrides[api.get_runtime_repo] = get_test_repo


def startup_test_api():
    """Override dependency for FastAPI."""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)
    global sessionfactory
    api.sessionfactory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    start_mappers()


# use a test startup event for API
api.core_api.router.on_startup = [startup_test_api]


def get_test_repo():
    """Override dependency function to get repo for FastAPI."""
    sessionRepo = ProjectRepository(api.sessionfactory())

    proj = model.Project("test", "test", "test")
    job = model.Job(
        "Test Name",
        "Test Description",
        status=model.Status.DONE,
        location="Test location",
    )
    obj1 = model.Object(1)
    obj1.add_detection(model.Detection(model.BBox(10, 20, 30, 40), 0.7, 1, 1))
    obj1.add_detection(model.Detection(model.BBox(15, 25, 35, 45), 0.6, 1, 2))
    obj1.add_detection(model.Detection(model.BBox(20, 30, 40, 50), 0.7, 2, 3))
    obj1.time_in = datetime(2020, 3, 28, 10, 20, 30)
    obj1.time_out = datetime(2020, 3, 28, 10, 30, 30)
    obj1.track_id = 1
    job.add_object(obj1)

    obj2 = model.Object(2)
    obj2.add_detection(model.Detection(model.BBox(40, 50, 60, 70), 0.7, 2, 2))
    obj2.add_detection(model.Detection(model.BBox(45, 55, 65, 75), 0.6, 2, 3))
    obj2.add_detection(model.Detection(model.BBox(50, 60, 70, 100), 0.7, 1, 4))
    obj2.time_in = datetime(2020, 3, 28, 20, 20, 30)
    obj2.time_out = datetime(2020, 3, 28, 20, 30, 30)
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
api.core_api.dependency_overrides[api.get_runtime_repo] = get_test_repo


def test_get_projects():
    """Test getting project list endpoint."""
    with TestClient(api.core_api) as client:
        response = client.get("/projects/")

        assert response.status_code == 200


def test_add_project():
    """Test posting a new project."""
    with TestClient(api.core_api) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 201
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
            "job_count": 0,
        }


def test_add_project_with_location():
    """Test posting a new project with location string."""
    with TestClient(api.core_api) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
                "location": "Testing",
            },
        )
        assert response.status_code == 201
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
            "job_count": 0,
        }


def test_get_project():
    """Test retrieving a single project."""
    with TestClient(api.core_api) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response_post_project.status_code == 201

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
    with TestClient(api.core_api) as client:
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 201
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Job name",
                "description": "Job description",
                "location": "test",
                "videos": [],
            },
        )

        assert response_job.status_code == 201

        job_data = response_job.json()
        assert "id" in job_data
        job_id = job_data["id"]

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
                "videos": [],
                "location": "test",
            }
        ]


def test_get_job():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(api.core_api) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response_post_project.status_code == 201

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
            json={
                "name": "Job name",
                "description": "Job description",
                "videos": [],
                "location": "test",
            },
        )
        assert response_post_job.status_code == 201

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
            "videos": [],
            "location": "test",
        }

        response = client.get(f"/projects/999999/jobs/{job_id}")
        assert response.status_code == 404

        response = client.get(f"/projects/{project_id}/jobs/99999")
        assert response.status_code == 404


def test_get_done_job():
    """Test completed job with objects."""
    with TestClient(api.core_api) as client:
        response = client.get("/projects/1/jobs/")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1

        assert "id" in data[0]
        assert "_status" in data[0]
        assert "_objects" in data[0]

        objs = data[0]["_objects"]
        assert len(objs) == 2

        for obj in objs:
            assert "label" in obj
            assert "probability" in obj
            assert "track_id" in obj
            assert "time_in" in obj
            assert "time_out" in obj


def test_project_not_existing():
    """Test posting a new job to a project and getting list of jobs."""
    with TestClient(api.core_api) as client:

        response = client.get(f"/projects/0/jobs")
        assert response.status_code == 404

        response = client.get(f"/projects/abc/jobs")
        assert response.status_code == 422

        response = client.post(
            "/projects/-1/jobs/",
            json={
                "name": "Job name",
                "description": "Job description",
                "videos": [],
                "location": "test",
            },
        )
        assert response.status_code == 404


def test_pause_job():
    """Test pausing of a job."""
    with TestClient(api.core_api) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )

        project_data = response_post_project.json()
        project_id = project_data["id"]

        response_post_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Job name",
                "description": "Job description",
                "videos": [],
                "location": "test",
            },
        )

        job_data = response_post_job.json()
        job_id = job_data["id"]

        response_wrong_project = client.post(
            f"/projects/{project_id+99999}/jobs/{job_id}/pause"
        )
        assert response_wrong_project.status_code == 404

        response_wrong_job = client.post(
            f"/projects/{project_id}/jobs/{job_id+99999}/pause"
        )
        assert response_wrong_job.status_code == 404

        response_start_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/pause",
        )
        assert response_start_job.status_code == 202


def test_start_job():
    """Test starting a job."""
    with TestClient(api.core_api) as client:
        response_post_project = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )

        project_data = response_post_project.json()
        project_id = project_data["id"]

        response_post_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Job name",
                "description": "Job description",
                "videos": [],
                "location": "test",
            },
        )

        job_data = response_post_job.json()
        job_id = job_data["id"]

        response_wrong_project = client.post(
            f"/projects/{project_id+99999}/jobs/{job_id}/start"
        )
        assert response_wrong_project.status_code == 404

        response_wrong_job = client.post(
            f"/projects/{project_id}/jobs/{job_id+99999}/start"
        )
        assert response_wrong_job.status_code == 404

        response_start_job = client.post(
            f"/projects/{project_id}/jobs/{job_id}/start",
        )
        assert response_start_job.status_code == 202


def test_add_and_get_job_with_videos():
    """Test posting a new job to a project with videos."""
    with TestClient(api.core_api) as client:
        # Setup of a project to test with
        response = client.post(
            "/projects/",
            json={
                "name": "Project name",
                "number": "AB-123",
                "description": "A project description",
            },
        )
        assert response.status_code == 201
        project_data = response.json()
        assert "id" in project_data
        project_id = project_data["id"]

        # Test adding job with valid path to a video
        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Job name",
                "description": "Job description",
                "location": "test",
                "videos": [
                    "./tests/integration/test-abbor[2021-01-01_00-00-00]-000-small.mp4"
                ],
            },
        )

        assert response_job.status_code == 201

        # Test adding job with not a valid path to video
        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Bad job",
                "description": "Bad job description",
                "location": "bad location",
                "videos": ["./video_not_existing.mp4"],
            },
        )

        assert response_job.status_code == 415

        # Test adding job with not a valid timestamp to video
        response_job = client.post(
            f"/projects/{project_id}/jobs/",
            json={
                "name": "Bad job",
                "description": "Bad job description",
                "location": "bad location",
                "videos": ["./tests/integration/test-abbor.mp4"],
            },
        )

        assert response_job.status_code == 415
