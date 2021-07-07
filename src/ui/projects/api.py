"""Blueprint for the projects module."""
import functools
import json
import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import requests

from ui.projects.model import Job, JobBare, Project, ProjectBare

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

T = TypeVar("T")
Result = Optional[T]
F = TypeVar("F", bound=Callable[..., Any])


class Client:
    """API client class.

    Wrapping the error handling of `requests` calls to api by using the
    `API.call` decorator.

    Attributes
    ----------
    _session    :   requests.Session
                    Keeps Session between calls.

    _endpont        str
                    URL of the API endpoint.

    Parameters
    ----------
    endpoint    :   str
                    URL of the API endpoint.

    Methods
    -------
    get(uri: str)
        Perform a GET request to `uri`.
    post(uri: str, data: Dict[str, Any])
        Perform a POST request to `uri` with `data` as body of request.
    create(uri: str, data: Dict[str, Any])
        Perform a POST request to `uri` with `data` as body of request.
    get_projects()
        Get all projects.
    get_project(project_id: int)
        Get a single project.
    post_project(project: Project)
        Create a new `Project`
    get_job(project_id: int, job_id: int)
        Get a single `Job`.
    post_job(project_id, job: Job)
        Create a new `Job` in project with `project_id`.
    change_job_status(project_id: int, job_id: int)
        Toggle the processing status of a `Job`

    Examples
    --------
    >>> endpoint = "http://127.0.0.1:8000"
    >>> client = Client(endpoint)
    >>> response = client.get(f"{endpoint}/projects/")
    """

    def __init__(self, endpoint: str) -> None:
        self._session: requests.Session = requests.Session()
        self._endpoint: str = endpoint

    class Api:
        """Api decorator class."""

        @classmethod
        def call(
            cls,
            request: Optional[F] = None,
            *,
            status_code: int = 200,
            acceptable_error: Optional[int] = None,
        ) -> Callable:
            """Handle errors for api call.

            Used as decorator on `Client` methods calling HTTP Methods to API.

            Parameters
            ----------
            request     :       Callable
                                Function calling API.
            status_code :       int
                                Success status_code from API.
            acceptable_error :  int
                                Alternative error code that should
                                return response.
            """

            def decorator_call(request: F) -> F:
                functools.wraps(request)

                def wrapper_call(*args, **kwargs) -> Result[requests.Response]:  # type: ignore
                    try:
                        response = request(*args, **kwargs)  # type: ignore
                    except requests.ConnectionError as e:
                        logger.warning(
                            f"ConnectionError: {request.__name__} - "
                            f"{request.__dict__} - {repr(e)}"
                        )
                        return None

                    if (
                        not response.status_code == status_code
                        and acceptable_error is None
                    ):
                        logger.warning(
                            "Status code: %s, error: %s",
                            response.status_code,
                            response.json(),
                        )
                        return None

                    return response

                return cast(F, wrapper_call)

            if request is None:
                return decorator_call
            else:
                return decorator_call(request)

    @Api.call(status_code=200)
    def get(self, uri: str, params: Dict = {}) -> requests.Response:
        """Perform a GET request to `uri.

        Expects a successful call to return a status_code = 200.

        Parameters
        ----------
        uri     :   str
                    API endpoint.

        Returns
        -------
        Optional[requests.Response]
            Returns a `Response` if no errors, else `None`

        See Also
        --------
        api.call : Decorator the handles the API calls.
        """
        logger.info("get from %s", uri)
        return self._session.get(uri, params=params)

    @Api.call(status_code=201, acceptable_error=415)
    def post(
        self, uri: str, data: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """Perform a POST request to `uri` with `data` as body of request.

        Expects a successful call to return a status_code = 200.

        Parameters
        ----------
        uri     :   str
                    API endpoint.
        data    :   Dict[str, Any]
                    Data to be posted as request body.

        Returns
        -------
        Optional[requests.Response]
            Returns a `Response` if no errors, else `None`

        See Also
        --------
        api.call : Decorator the handles the API calls.
        """
        logger.info("post to %s, %s", uri, data)
        return self._session.post(uri, json=data)

    @Api.call(status_code=202)
    def toggle(self, uri: str) -> requests.Response:
        """Perform a POST request to `uri`.

        Expects a successful call to return a status_code = 202.

        Parameters
        ----------
        uri     :   str
                    API endpoint.

        Returns
        -------
        Optional[requests.Response]
            Returns a `Response` if no errors, else `None`

        See Also
        --------
        api.call : Decorator that handles the API calls.
        """
        logger.info("post to %s", uri)
        return self._session.post(uri)

    def get_projects(
        self, page: int = 1, per_page: int = 10
    ) -> Optional[Tuple[List[ProjectBare], int]]:
        """Get all projects from endpoint.

        Parameters
        ----------
        page : int
            Specific page to get.
        per_page : int
            Number of pages per page to pull.

        Returns
        -------
        Union[Tuple[Optional[List[ProjectBare]], int], None]
                    List of all `Project` from `core` or None.
        """
        payload = {"page": page, "per_page": per_page}
        result = self.get(f"{self._endpoint}/projects/", params=payload)

        if not isinstance(result, requests.Response):
            return None

        if not result.headers["x-total"]:
            return None

        return [ProjectBare(**p) for p in result.json()], int(
            result.headers["x-total"]
        )

    def get_project(
        self,
        project_id: int,
    ) -> Optional[ProjectBare]:
        """Get one project from endpoint.

        Parameters
        ----------
        project_id  :   int
                        Id of project to get.

        Returns
        -------
        Optional[ProjectBare]
                    Project from core with `project_id`.
        """
        result = self.get(
            f"{self._endpoint}/projects/{project_id}",
        )

        if isinstance(result, requests.Response):
            return ProjectBare(**result.json())  # type: ignore

        return None

    def post_project(self, project: Project) -> None:
        """Post project from endpoint.

        Parameters
        ----------
        project     :   Project
                        Project to send to `core` api.
        """
        result = self.post(
            f"{self._endpoint}/projects/", project.to_post_dict()
        )  # type: ignore

        if isinstance(result, requests.Response):
            logger.info(
                "Project %s posted with status_code: %s",
                project.id,
                result.status_code,
            )

        return None

    def get_jobs(
        self,
        project_id: int,
        page: int = 1,
        per_page: int = 10,
    ) -> Optional[Tuple[List[JobBare], int]]:
        """Get a list of jobs from the endpoint.

        Parameters
        ----------
        project_id  :   int
                        Project to send to `core` api.
        page        :   int
                        Selected page.
        per_page    :   int
                        Per page count.

        Returns
        -------
        Optional[List[Job]]
                    List of `Job` from `core`.
        """
        result_project = self.get(f"{self._endpoint}/projects/{project_id}")

        payload = {"page": page, "per_page": per_page}
        result_jobs = self.get(
            f"{self._endpoint}/projects/{project_id}/jobs/", params=payload
        )

        if not isinstance(result_project, requests.Response) or not isinstance(
            result_jobs, requests.Response
        ):
            return None

        if not result_jobs.headers["x-total"]:
            return None

        return [
            JobBare.from_dict(j, project_id, result_project.json()["name"])
            for j in result_jobs.json()
        ], int(result_jobs.headers["x-total"])

    def get_job(self, project_id: int, job_id: int) -> Optional[Job]:
        """Get a single job from the endpoint.

        Parameters
        ----------
        project_id  :   Project ID
                        Project to send to `core` api.
        job_id      :   Job ID
                        Job to send to `core` api.

        Returns
        -------
        Optional[Job]
                    Single `Job` from `core`.
        """
        result_project = self.get(f"{self._endpoint}/projects/{project_id}")
        result_job = self.get(
            f"{self._endpoint}/projects/{project_id}/jobs/{job_id}"
        )

        if isinstance(result_project, requests.Response) and isinstance(
            result_job, requests.Response
        ):
            return Job.from_dict(
                result_job.json(), project_id, result_project.json()["name"]  # type: ignore
            )

        return None

    def post_job(self, project_id: int, job: Job) -> Optional[int]:
        """Post a single job to the endpoint.

        Parameters
        ----------
        project_id  :   Project ID
                        Project to send to `core` api.
        job         :   Job
                        Job to send to `core` api.

        Returns
        -------
        Optional[Job]
                    Single `Job` from `core`.
        """
        result = self.post(  # type:ignore
            f"{self._endpoint}/projects/{project_id}/jobs",
            job.to_post_dict(),
        )

        if not isinstance(result, requests.Response):
            return None

        try:
            job_id = result.json()["id"]
            logger.info(
                "Job no. %s posted to project no. %s with status_code: %s",
                job_id,
                project_id,
                result.status_code,
            )
            return job_id
        except KeyError as e:
            logger.error("no job id returned from core, msg: %s", e)
            return result.json()["detail"]

    def change_job_status(
        self, project_id: int, job_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """Change job status.

        Parameters
        ----------
        project_id  :   Project ID
                        Project to send to `core` api.
        job_id      :   Job ID
                        Job to send to `core` api.

        Returns
        -------
        Tuple[Optional[str], Optional[str]]
                        Tuple container the old and new status for a
                        job.
        """
        job = self.get_job(project_id, job_id)  # type: ignore

        if job is None:
            return (None, None)

        old_status = job.get_status()
        new_status: str = ""

        if old_status == "pending":
            # type:ignore
            r_post = self.toggle(
                f"{self._endpoint}/projects/{project_id}/jobs/{job_id}/start",
            )

            if r_post is None:
                return (None, None)

            new_status = "queued"
        else:
            new_status = "done"

        return old_status, new_status  # type: ignore

    def check_api(self) -> bool:
        """Check if API responds.

        Returns
        -------
        bool
            Wether the API is online or not.
        """
        try:
            self._session.get(f"{self._endpoint}")  # type: ignore
        except requests.ConnectionError:
            return False

        return True
