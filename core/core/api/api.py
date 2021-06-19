"""Core REST control API.

Package defining core's API for use by _view's_. Documentation of the
API specification can be accesses at ``localhost:8000/docs`` when the
server is running.
"""
import logging
from typing import Dict, List

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from fastapi.responses import StreamingResponse

import core.api.schema as schema
import core.main
from core import model, services
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.object import (
    SqlAlchemyObjectRepository as ObjectRepository,
)
from core.repository.video import SqlAlchemyVideoRepository as VideoRepostory
from core.utils import outline_detection

logger = logging.getLogger(__name__)

core_api = FastAPI()


def get_runtime_repo():  # noqa: D403
    """FastAPI dependencies function creating `repositories` for endpoint."""
    # Map DB to Objects.
    sessionRepo = ProjectRepository(core.main.sessionfactory())
    logger.debug("Repository created.")
    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


def convert_to_projectbare(project: model.Project) -> schema.ProjectBare:
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


def convert_to_jobbare(job: model.Job) -> schema.JobBare:
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
    if not isinstance(job, model.Job):
        raise TypeError(
            f"{type(job)} in not of type model.Job.",
        )

    return schema.JobBare(
        id=job.id,
        status=job._status,
        name=job.name,
        description=job.description,
        location=job.location,
        object_count=len(job._objects),
        video_count=len(job.videos),
        progress=job.progress,
    )


def construct_pagination_data(
    count: int, page: int, per_page: int
) -> Dict[str, str]:
    """Create pagination data for easy usage when contruction routes.

    The function returns a dict which has all it values calculated
    from the parameters sent to the route.

    Parameters
    ----------
    count : int
        Number of items returned by the database.
    page: int
        Current page the route is serving.
    per_page: int
        Number of items per page.

    Returns
    -------
    parameters : dict
        Complete dictionary with computed data.
    """
    pagination: Dict = dict()

    pagination["x-total"] = f"{count}"
    pagination["x-page"] = f"{page}"
    pagination["x-per-page"] = f"{per_page}"

    total_pages: int = int(count / per_page) + 1
    pagination["x-total-pages"] = f"{total_pages}"

    prev_page = (page - 1) if page > 1 else page
    next_page = (page + 1) if page < total_pages else page

    if page > total_pages:
        prev_page = (total_pages - 1) if total_pages > 1 else total_pages
        next_page = total_pages

    pagination["x-prev-page"] = f"{prev_page}"
    pagination["x-next-page"] = f"{next_page}"

    return pagination


@core_api.get("/projects/", response_model=List[schema.ProjectBare])
def list_projects(
    response: Response,
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

    # Calculate the pagination data.  This needs early calculation
    # because we need the headers anyway.
    pagination_response = construct_pagination_data(list_length, page, per_page)

    # Populate the headers with the pagination data.
    for k, v in pagination_response.items():
        response.headers[k] = v

    # Return early if no projects in database.
    if list_length == 0:
        return []

    # Set to - 1 because page != index in a list.
    begin_idx = (page - 1) * per_page
    end_idx = begin_idx + per_page

    if end_idx > list_length:
        end_idx = list_length

    resp: List[schema.ProjectBare] = list()

    for proj in repo.list()[slice(begin_idx, end_idx)]:
        try:
            resp.append(convert_to_projectbare(proj))
        except TypeError as e:  # pragma: no cover
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
    new_project = repo.add(model.Project(**project.dict()))

    return convert_to_projectbare(new_project)


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

    return convert_to_projectbare(project)


@core_api.get(
    "/projects/{project_id}/jobs/", response_model=List[schema.JobBare]
)
def list_project_jobs(
    project_id: int,
    response: Response,
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
    if not project:
        logger.warning("Project %s not found,", project_id)
        raise HTTPException(status_code=404, detail="Project not found")

    list_length = project.number_of_jobs

    # Calculate the pagination data.  This needs early calculation
    # because we need the headers anyway.
    pagination_response = construct_pagination_data(list_length, page, per_page)

    # Populate the headers with the pagination data.
    for k, v in pagination_response.items():
        response.headers[k] = v

    if list_length == 0:
        return []

    # Set to - 1 because page != index in a list.
    begin_idx = (page - 1) * per_page
    end_idx = begin_idx + per_page

    if end_idx > list_length:
        end_idx = list_length

    resp: List[schema.JobBare] = list()

    for job in project.jobs[slice(begin_idx, end_idx)]:
        try:
            resp.append(convert_to_jobbare(job))
        except TypeError as e:  # pragma: no cover
            logger.warning(e)

    return resp


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


@core_api.get("/objects/{object_id}/preview")
async def get_object_image(object_id: int = Path(..., ge=1)):
    """Display a preview video of an Object.

    Returns
    -------
    Streamingresponse
        A video stream.

    Raises
    ------
    HTTPException
        If no object is found.
    """
    if core.main.sessionfactory is None:  # pragma: no cover
        raise RuntimeError("Sessionfactory is not made")

    session = core.main.sessionfactory()

    o_repo = ObjectRepository(session)
    v_repo = VideoRepostory(session)

    obj = o_repo.get(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    def gen():
        prev_video_id = -1
        vid = None

        for frame_id, video_id, bbx in obj.get_frames():
            if video_id is not None and frame_id is not None:
                if video_id is not prev_video_id:
                    vid = v_repo.get(video_id)

                frame = vid[frame_id]

                img = outline_detection(frame, bbx)

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + bytearray(img)
                    + b"\r\n"
                )

    return StreamingResponse(
        gen(), media_type="multipart/x-mixed-replace;boundary=frame"
    )
