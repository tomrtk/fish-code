"""Blueprint for the projects module."""
import functools
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

import requests

from ui.projects.model import Job, Project, ProjectBare

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

T = TypeVar("T")
Result = Optional[T]


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
            request: Callable = None,
            *,
            status_code: int = 200,
            acceptable_error: int = None,
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

            def decorator_call(request):
                functools.wraps(request)

                def wrapper_call(*args, **kwargs) -> Result[requests.Response]:
                    try:
                        response = request(*args, **kwargs)  # type: ignore
                    except requests.ConnectionError as e:
                        logger.warning(
                            "ConnectionError:",
                            request.__name__,
                            request.__dict__,
                            e,
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

                return wrapper_call

            if request is None:
                return decorator_call
            else:
                return decorator_call(request)

    @Api.call(status_code=200)
    def get(self, uri: str) -> requests.Response:
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
        return self._session.get(uri)

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
        logger.info("post to %s, %s", uri)
        return self._session.post(uri)

    def get_projects(self) -> Optional[List[ProjectBare]]:
        """Get all projects from endpoint.

        Returns
        -------
        Optional[List[ProjectBare]]
                    List of all `Project` from `core`.
        """
        result = self.get(f"{self._endpoint}/projects/")

        if isinstance(result, requests.Response):
            return [ProjectBare(**p) for p in result.json()]  # type: ignore

        return None

    def get_project(self, project_id: int) -> Optional[ProjectBare]:
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
        result = self.get(f"{self._endpoint}/projects/{project_id}")

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

    def get_jobs(self, project_id: int) -> Optional[List[Job]]:
        """Get a list of jobs from the endpoint.

        Parameters
        ----------
        project_id  :   int
                        Project to send to `core` api.

        Returns
        -------
        Optional[List[Job]]
                    List of `Job` from `core`.
        """
        result_project = self.get(f"{self._endpoint}/projects/{project_id}")
        result_jobs = self.get(f"{self._endpoint}/projects/{project_id}/jobs/")

        if isinstance(result_project, requests.Response) and isinstance(
            result_jobs, requests.Response
        ):
            return [
                Job.from_dict(j, project_id, result_project.json()["name"])
                for j in result_jobs.json()
            ]

        return None

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
            return result.json()["id"]
        except KeyError as e:
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

        if old_status == "pending" or old_status == "paused":
            # type:ignore
            r_post = self.toggle(
                f"{self._endpoint}/projects/{project_id}/jobs/{job_id}/start",
            )

            if r_post is None:
                return (None, None)

            new_status = "running"
        elif old_status == "running":
            # type:ignore
            r_post = self.toggle(
                f"{self._endpoint}/projects/{project_id}/jobs/{job_id}/pause",
            )

            if r_post is None:
                return (None, None)

            new_status = r_post.json().get("_status", "").lower()
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
