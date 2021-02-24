import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core.api import core, make_db
from core.repository.orm import metadata, start_mappers


def make_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()
    try:
        yield session()
    finally:
        clear_mappers()


core.dependency_overrides[make_db] = make_test_db
client = TestClient(core)


def test_get_projects():
    response = client.get("/projects/")

    assert response.status_code == 200


def test_post_project():
    response = client.post(
        "/projects/",
        json={
            "name": "Project name",
            "number": "AB-123",
            "description": "A project description",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Project name",
        "number": "AB-123",
        "description": "A project description",
        "jobs": {},
    }
