"""Core REST control API.

Package defining core's API for use by _view's_. Documentation of the
API specification can be accesses at ``localhost:8000/docs`` when the
server is running.
"""
import logging
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, clear_mappers, scoped_session, sessionmaker
from sqlalchemy.orm.session import close_all_sessions

import core.api.schema as schema
from core import model, services
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)

core_api = FastAPI()

engine = create_engine(
    "sqlite:///data.db",
    connect_args={"check_same_thread": False},
)
# Create tables from defined schema.
metadata.create_all(engine)

# Make a scoped session to be used by other threads in processing.
# https://docs.sqlalchemy.org/en/13/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session
sessionfactory = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


@core_api.on_event("startup")
def startup():
    """Start mappings at api start."""
    start_mappers()
    logger.debug("Database connected.")


@core_api.on_event("shutdown")
def shutdown():
    """Cleanup on shutdown of api."""
    close_all_sessions()
    clear_mappers()


def get_runtime_repo():  # noqa: D403
    """FastAPI dependencies function creating `repositories` for endpoint."""
    # Map DB to Objects.
    sessionRepo = ProjectRepository(sessionfactory())
    logger.debug("Repository created.")
    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


def convert_to_bare(project: model.Project) -> schema.ProjectBare:
    """Convert `model.Project` to `schema.ProjectBare`.

    Parameters
    ----------
    data : model.Project
        The data to convert from.

    Returns
    -------
    schema.Project
        Converted data from model to schema object.

    Raises
    ------
    TypeError
        When neither valid type is passed.
    """
    if not isinstance(project, model.Project):
        raise TypeError(
            f"{type(project)} in not of type model.Project.",
        )

    return schema.ProjectBare(
        id=project.id,
        name=project.name,
        number=project.number,
        description=project.description,
        location=project.location,
        job_count=len(project.jobs),
    )


@core_api.get("/projects/", response_model=List[schema.ProjectBare])
def list_projects(
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
    page: int = Query(
        1,
        ge=1,
        description="Select which page to fetch.",
    ),
    per_page: int = Query(
        10, ge=1, description="Choose how many items per page."
    ),
):
    """List all projects.

    Endpoint returns a list of all projects to GET requests.

    The endpoint supports using pagination by configure `page` and
    `per_page`.

    Parameters
    ----------
    - page : int
        Select which page to fetch.
    - per_page : int
        Choose how many items per page.

    Returns
    -------
    List[schema.ProjectBare]
        List of all `Project`.
    """
    list_length = len(repo.list())

    if list_length:
        return []

    # Set to - 1 because page != index in a list.
    begin_idx = (page - 1) * per_page
    end_idx = begin_idx + per_page

    if end_idx > list_length:
        end_idx = list_length

    resp: List[schema.ProjectBare] = list()

    for proj in repo.list()[slice(begin_idx, end_idx)]:
        try:
            resp.append(convert_to_bare(proj))
        except TypeError as e:
            logger.warning(e)

    return resp


@core_api.post(
    "/projects/",
    response_model=schema.ProjectBare,
    status_code=status.HTTP_201_CREATED,
)
def add_project(
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
    return convert_to_bare(repo.add(model.Project(**project.dict())))


@core_api.get("/projects/{project_id}/", response_model=schema.ProjectBare)
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

    return convert_to_bare(project)


@core_api.get("/projects/{project_id}/jobs/", response_model=List[schema.Job])
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


@core_api.post(
    "/projects/{project_id}/jobs/", status_code=status.HTTP_201_CREATED
)
def add_job_to_project(
    project_id: int,
    job: schema.JobCreate,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
):
    """Add a `Job` to a `Project` who has`project_id`.

    Returns
    -------
    id :
        The id of Job, {"id": int}

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
        errors: Dict[str, List[str]] = dict()
        file_not_found = []
        time_not_found = []
        for video_path in job.videos:
            try:
                videos.append(model.Video.from_path(video_path))
            except FileNotFoundError:
                file_not_found.append(video_path)
            except model.TimestampNotFoundError:
                time_not_found.append(video_path)

        errors["FileNotFoundError"] = file_not_found
        errors["TimestampNotFoundError"] = time_not_found

        if len(file_not_found) > 0 or len(time_not_found) > 0:
            raise HTTPException(
                status_code=415,
                detail=errors,
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


@core_api.get("/projects/{project_id}/jobs/{job_id}", response_model=schema.Job)
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


@core_api.post(
    "/projects/{project_id}/jobs/{job_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
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

    services.queue_job(project_id, job_id, repo.session)


@core_api.post(
    "/projects/{project_id}/jobs/{job_id}/pause",
    status_code=status.HTTP_202_ACCEPTED,
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

    # TODO: Schedule a job to be paused

    return job
