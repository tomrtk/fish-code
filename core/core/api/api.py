"""Core REST control API.

Package defining core's API for use by _view's_. Documentation of the
API specification can be accesses at ``localhost:8000/docs`` when the
server is running.
"""
import logging
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

import core.api.schema as schema
from core import model
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)

core = FastAPI()


def make_db():  # noqa: D403
    """FastAPI dependencies function creating a database connection."""
    # Setup of runtime stuff. Should be moved to its own place later.
    engine = create_engine(
        "sqlite:///data.db",
        connect_args={"check_same_thread": False},
    )
    # Create tables from defines schema.
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()
    logger.debug("Database connected.")
    try:
        yield session()
    finally:
        clear_mappers()


def get_runtime_repo(session=Depends(make_db)):  # noqa: D403
    """FastAPI dependencies function creating `repositories` for endpoint."""
    # Map DB to Objects.
    sessionRepo = ProjectRepository(session)
    logger.debug("Repository created.")
    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


@core.get("/projects/", response_model=List[schema.Project])
def list_projects(
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False)
):
    """List all projects.

    Endpoint returns a list of all projects to GET requests.

    Returns
    -------
    List[Project]
        List of all `Project`.
    """
    return repo.list()


@core.post("/projects/", response_model=schema.Project)
def add_projects(
    project: schema.ProjectCreate,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Add a project to the system.

    Add project on POST request on endpoint.

    Returns
    -------
    Project
        New `Project` with `id`.
    """
    return repo.add(model.Project(**project.dict()))


@core.get("/projects/{project_id}/", response_model=schema.Project)
def get_project(
    project_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Retrieve a single project.

    Get a project from a GET request on endpoint.

    Returns
    -------
    Project
        Single project from project_id

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    """
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@core.get("/projects/{project_id}/jobs/", response_model=List[schema.Job])
def list_project_jobs(
    project_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """List all jobs associated with Project with _project_id_.

    Endpoint returns a list of Jobs from Project with _project_id_.

    Returns
    -------
    List[Job]
        List of all jobs associated with project.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    """
    project = repo.get(project_id)
    if project:
        jobs = project.get_jobs()
        return jobs
    else:
        logger.warning("Project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")


@core.post("/projects/{project_id}/jobs/", status_code=status.HTTP_201_CREATED)
def add_job_to_project(
    project_id: int,
    job: schema.JobCreate,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Add a `Job` to a `Project` who has`project_id`.

    Returns
    -------
    Job
        New job with `id`.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    HTTPException
        If video path is not found. Status code: 404.
    """
    project = repo.get(project_id)
    if project:
        # Create videos from list of paths
        videos: List[model.Video] = []
        errors = []
        for video_path in job.videos:
            try:
                videos.append(model.Video.from_path(video_path))
            except FileNotFoundError:
                errors.append(video_path)

        if len(errors) > 0:
            raise HTTPException(
                status_code=404, detail=f"Videos not found, paths: {errors}"
            )

        # create dict and remove videos from dict
        job_dict = job.dict()
        job_dict.pop("videos", None)
        new_job = model.Job(**job_dict)

        # Add each video to new job
        for video in videos:
            new_job.add_video(video)

        # add job to project and save repo
        project = project.add_job(new_job)
        repo.save()

        logger.debug("Job %s added to project %s", job, project_id)
        return {"id": new_job.id}

    else:
        logger.warning("Job not added, project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")


@core.get("/projects/{project_id}/jobs/{job_id}", response_model=schema.Job)
def get_job_from_project(
    project_id: int,
    job_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Retrieve a single job from a project.

    Returns
    -------
    Job
        Job with `job_id`.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    HTTPException
        If no job with _job_id_ found. Status code: 404.
    """
    project = repo.get(project_id)

    if not project:
        logger.warning("Project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")
    elif project.get_job(job_id) is None:
        logger.warning("Job %s not found,", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    return project.get_job(job_id)


@core.post(
    "/projects/{project_id}/jobs/{job_id}/start", response_model=schema.Job
)
def set_job_status_start(
    project_id: int,
    job_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Mark the job to be processed.

    Returns
    -------
    Job
        Job with updated status.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    HTTPException
        If no job with _job_id_ found. Status code: 404.
    HTTPException
        If job is already running or completed. Status code: 403.
    """
    project = repo.get(project_id)

    if not project:
        logger.warning("Project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")

    job = project.get_job(job_id)

    if job is None:
        logger.warning("Job %s not found,", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.start()
        repo.save()
    except model.JobStatusException:
        logger.warning(
            "Cannot start job %s, it's already running or completed.", job_id
        )
        raise HTTPException(
            status_code=403,
            detail="Cannot start job, it's already running or completed.",
        )

    return job


@core.post(
    "/projects/{project_id}/jobs/{job_id}/pause", response_model=schema.Job
)
def set_job_status_pause(
    project_id: int,
    job_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Mark the job to be paused.

    Returns
    -------
    Job
        Job with updated status.

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    HTTPException
        If no job with _job_id_ found. Status code: 404.
    HTTPException
        If job is already paused or completed. Status code: 403.
    """
    project = repo.get(project_id)

    if not project:
        logger.warning("Project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")

    job = project.get_job(job_id)

    if job is None:
        logger.warning("Job %s not found,", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        job.pause()
        repo.save()
    except model.JobStatusException:
        logger.warning("Cannot pause job %s, it's not running..", job_id)
        raise HTTPException(
            status_code=403, detail="Cannot pause job, it's not running.."
        )

    return job
