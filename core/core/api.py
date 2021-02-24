"""Core REST API """
from typing import Dict, List
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core import model
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

core = FastAPI()


def make_db():
    # Setup of runtime stuff. Should be moved to its own place later.
    engine = create_engine(
        # "sqlite:///:memory:",
        "sqlite:///data.db",
        connect_args={"check_same_thread": False},
    )
    # Create tables from defines schema.
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()
    try:
        yield session()
    finally:
        clear_mappers()


# API dependecy
def get_runtime_repo(session=Depends(make_db)):
    # Map DB to Objects.
    sessionRepo = ProjectRepository(session)
    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


# pydantic schema
class JobBase(BaseModel):
    name: str


class Job(JobBase):
    id: int
    status: model.Status

    class Config:
        orm_mode = True


class JobCreate(JobBase):
    pass


class ProjectBase(BaseModel):
    name: str
    number: str
    description: str


class Project(ProjectBase):
    id: int
    jobs: Dict[int, Job] = {}

    class Config:
        orm_mode = True


class ProjectCreate(ProjectBase):
    pass


# API
@core.get("/projects/", response_model=List[Project])
def list_projects(repo: ProjectRepository = Depends(get_runtime_repo)):
    """List all projects.
    Endpoint returns a list of all projects to GET requests.
    """
    return repo.list()


@core.post("/projects/", response_model=Project)
def add_projects(
    project: ProjectCreate, repo: ProjectRepository = Depends(get_runtime_repo)
):
    """Add a project to the system.
    Add project on POST request on endpoint.
    """
    return repo.add(model.Project(**project.dict()))


@core.get("/projects/{project_id}/jobs/", response_model=List[Job])
def list_project_jobs(
    project_id: int, repo: ProjectRepository = Depends(get_runtime_repo)
):
    """List all jobs associated with Project with _project_id_.

    Endpoint returns a list of Jobs from Project with _project_id_. If
    project not found raises a __HTTPException__ with status code 404.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found.
    """
    project = repo.get(project_id)
    if project:
        jobs = project.get_jobs()
        return jobs
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@core.post("/projects/{project_id}/jobs/", response_model=Job)
def add_job_to_project(
    project_id: int,
    job: JobCreate,
    repo: ProjectRepository = Depends(get_runtime_repo),
):
    pass  # Missing functionality in repository
