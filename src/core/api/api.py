"""Core REST control API.

Package defining core's API for use by _view's_. Documentation of the
API specification can be accesses at ``localhost:8000/docs`` when the
server is running.
"""

import asyncio
import base64
import binascii
import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any, Union

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
from config import load_config
from core import model, services
from core.api import utils
from core.repository.object import (
    SqlAlchemyObjectRepository as ObjectRepository,
)
from core.repository.project import (
    SqlAlchemyProjectRepository as ProjectRepository,
)
from core.repository.video import SqlAlchemyVideoRepository as VideoRepostory
from core.services import get_directory_listing
from core.utils import outline_detection

logger = logging.getLogger(__name__)
config = load_config()

core_api = FastAPI()


def get_runtime_repo() -> Generator[ProjectRepository, None, None]:
    """Fastapi dependencies function creating `repositories` for endpoint."""
    # Map DB to Objects.
    assert core.main.sessionfactory is not None
    sessionRepo = ProjectRepository(core.main.sessionfactory())
    logger.debug("Repository created.")
    try:
        yield sessionRepo
    finally:
        sessionRepo.session.commit()
        sessionRepo.session.close()


def construct_pagination_data(
    count: int,
    page: int,
    per_page: int,
) -> dict[str, str]:
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
    pagination: dict = {}

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


@core_api.get("/projects/", response_model=list[schema.ProjectBare])
def list_projects(
    response: Response,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
    page: int = Query(
        1,
        ge=1,
        description="Select which page to fetch.",
    ),
    per_page: int = Query(
        10,
        ge=1,
        description="Choose how many items per page.",
    ),
) -> list[schema.ProjectBare]:
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

    resp: list[schema.ProjectBare] = []

    for proj in repo.list()[slice(begin_idx, end_idx)]:
        try:
            resp.append(utils.convert_to_projectbare(proj))
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
) -> schema.ProjectBare:
    """Add a project to the system.

    Add project on POST request on endpoint.

    Returns
    -------
    ProjectBare
        New `Project` with `id`.
    """
    new_project = repo.add(model.Project(**project.dict()))

    return utils.convert_to_projectbare(new_project)


@core_api.get("/projects/{project_id}/", response_model=schema.ProjectBare)
def get_project(
    project_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
) -> schema.ProjectBare:
    """Retrieve a single project.

    Get a project from a GET request on endpoint.

    Returns
    -------
    ProjectBare
        Single project from project_id

    Raises
    ------
    HTTPException
        If no project with _project_id_ found. Status code: 404.
    """
    project = repo.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return utils.convert_to_projectbare(project)


@core_api.get(
    "/projects/{project_id}/jobs/",
    response_model=list[schema.JobBare],
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
        10,
        ge=1,
        description="Choose how many items per page.",
    ),
) -> list[schema.JobBare]:
    """List all jobs associated with Project with _project_id_.

    Endpoint returns a list of Jobs from Project with _project_id_.

    Returns
    -------
    List[JobBare]
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

    resp: list[schema.JobBare] = []

    for job in project.jobs[slice(begin_idx, end_idx)]:
        try:
            resp.append(utils.convert_to_jobbare(job))
        except TypeError as e:  # pragma: no cover
            logger.warning(e)

    return resp


@core_api.post(
    "/projects/{project_id}/jobs/",
    status_code=status.HTTP_201_CREATED,
)
def add_job_to_project(
    project_id: int,
    job: schema.JobCreate,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
) -> dict[str, int]:
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
        videos: list[model.Video] = []
        errors: dict[str, list[str]] = {}
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
        assert new_job.id is not None

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
) -> model.Job:
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

    job = project.get_job(job_id)

    if job is None:
        logger.warning("Job %s not found,", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@core_api.post(
    "/projects/{project_id}/jobs/{job_id}/start",
    status_code=status.HTTP_202_ACCEPTED,
)
def set_job_status_start(
    project_id: int,
    job_id: int,
    repo: ProjectRepository = Depends(get_runtime_repo, use_cache=False),
) -> None:
    """Mark the job to be processed.

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


async def _frame_generator(
    obj: model.Object,
    video_repo: VideoRepostory,
) -> AsyncGenerator[bytes, None]:
    """Generate frames with marked object.

    For each frame the object is in view, yield the frame with marked object
    as a multipart stream response in bytes.

    Parameters
    ----------
    obj         :   Object
                    Object to preview
    video_repo  :   VideoRepostory
                    A video repository to collect videos from.

    Yields
    ------
    bytes
    """
    prev_video_id = -1
    vid = None

    for frame_id, video_id, bbx in obj.get_frames():
        if video_id is not None and frame_id is not None:
            if video_id is not prev_video_id:
                vid = video_repo.get(video_id)

            assert vid is not None

            frame = vid[frame_id]

            img = outline_detection(frame, bbx)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + bytearray(img) + b"\r\n"
            )


async def _stream(generator: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """Stream generator for preview of objects.

    Parameters
    ----------
    generator: AsyncGenerator
        Generator yielding one frame of an object at the time as an
        multipart stream response.

    Yields
    ------
    bytes
    """
    try:
        async for i in generator:
            yield i
            await asyncio.sleep(0.001)
    except asyncio.CancelledError:
        logger.info("cancelled preview of object")


@core_api.get("/objects/{object_id}/preview")
async def get_object_image(
    object_id: int = Path(..., ge=1),
) -> StreamingResponse:
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

    gen = _frame_generator(obj, v_repo)

    return StreamingResponse(
        _stream(gen),
        media_type="multipart/x-mixed-replace;boundary=frame",
    )


@core_api.get(
    "/projects/{project_id}/jobs/{job_id}/objects",
    response_model=dict[str, Any],
)
def get_objects_from_job(
    project_id: int = Path(..., ge=1),
    job_id: int = Path(..., ge=1),
    start: int = Query(0, ge=0),
    length: int = Query(10, ge=1),
) -> dict[str, Any]:
    """Endpoint to get part of objects from a job.

    Returns
    -------
    Dict[str, Any]
        Containing total number of object in job and part of objects from
        `start` to `start + length`.

    Raises
    ------
    HTTPException
        If no session to database can be established. Status code: 503.
    HTTPException
        If project or job id provided is not found. Status code: 422.
    """
    try:
        data = services.get_job_objects(project_id, job_id, start, length)
    except RuntimeError as e:
        raise HTTPException(503, repr(e))

    if data is None:
        msg = f"project with id {project_id} or job with id {job_id} not found"
        logger.warning(msg)
        raise HTTPException(422, msg)

    # convert to schema Object's:
    data["data"] = [schema.Object(**o.to_api()) for o in data["data"]]
    return data


@core_api.get("/storage", response_model=list[Union[dict[str, Any], str, None]])
async def get_storage() -> list[Union[dict[str, Any], str, None]]:
    """Get directory listing for a given path to a directory in jsTree json format.

    Returns
    -------
    Dict[str, Any]
        Json data explaining the file structure in jsTree format from video root directory.
        Does not run recursivly through all subfolders.

    Raises
    ------
    HTTPException
        If the path is a file, and not a directory.
    HTTPException
        If the path is invalid.
    """
    try:
        return get_directory_listing()
    except NotADirectoryError:
        logger.warning("Config parameter 'video_root_path' is not a directory.")
        raise HTTPException(
            status_code=400,
            detail="Video root is not a directory",
        )
    except FileNotFoundError:
        logger.warning(
            "Value of config parameter 'video_root_path' is invalid.",
        )
        raise HTTPException(
            status_code=404,
            detail="Video root folder could not be found.",
        )
    except PermissionError:
        logger.warning("Chosen path 'video_root_path' is not accessable.")
        raise HTTPException(
            status_code=403,
            detail="Chosen path is inaccessable",
        )


@core_api.get(
    "/storage/{path:str}",
    response_model=list[Union[dict[str, Any], str, None]],
)
async def get_storage_path(path: str) -> list[Union[dict[str, Any], str, None]]:
    """Get directory listing for a given path to a directory in jsTree json format.

    Parameters
    ----------
    path:   str
        Path to a folder as a string.  Must be a base64 encoded string.

    Returns
    -------
    Dict[str, Any]
        JSON data explaining the file structure in jsTree format for a folder.
        Does not run recursivly through all subfolders.

    Raises
    ------
    HTTPException
        If the path is a file, and not a directory.
    HTTPException
        If the path is invalid.
    """
    try:
        decrypted_path = base64.urlsafe_b64decode(path).decode()
    except binascii.Error:
        logger.warning(f"Unable to decode: '{path}'.")
        raise HTTPException(
            status_code=400,
            detail="Unable to decode path from parameter'",
        )

    try:
        return get_directory_listing(decrypted_path)
    except NotADirectoryError:
        logger.warning(f"Chosen path '{decrypted_path}' is not a directory.")
        raise HTTPException(
            status_code=400,
            detail="Chosen path is not a directory",
        )
    except FileNotFoundError:
        logger.warning(f"Chosen path '{decrypted_path}' is not valid.")
        raise HTTPException(status_code=404, detail="Chosen path is not valid")
    except PermissionError:
        logger.warning(f"Chosen path '{decrypted_path}' is not accessable.")
        raise HTTPException(
            status_code=403,
            detail="Chosen path is inaccessable",
        )
