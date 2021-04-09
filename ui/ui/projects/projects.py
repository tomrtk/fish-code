"""Blueprint for the projects module."""
import functools
import logging
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

import requests
from flask import (
    Blueprint,
    Config,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from ui.model import Detection, Job, Project, Video

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

root_folder = "~/Downloads"

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

    Methods
    -------
    get(uri: str)
        Perform a GET request to `uri`.
    post(uri: str, data: Dict[str, Any])
        Perform a POST request to `uri` with `data` as body of request.


    Examples
    --------
    >>> client = Client()
    >>> response = client.get("http://127.0.0.1:8000/projects/")
    """

    def __init__(self) -> None:
        self._session: requests.Session = requests.Session()

    class Api:
        """Api decorator class."""

        @classmethod
        def call(
            csl, request: Callable = None, *, status_code: int = 200
        ) -> Callable:
            """Handle errors for api call.

            Used as decorator on `Client` methods calling HTTP Methods to API.

            Parameters
            ----------
            request     :   Callable
                            Function calling API.
            status_code :   int
                            Success status_code from API.
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

                    if not response.status_code == status_code:
                        logger.warning(
                            "Status code: %s, error: %s",
                            response.status_code,
                            response.json().__dict__,
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
        """
        logger.info("get from %s", uri)
        return self._session.get(uri)

    @Api.call(status_code=200)
    def post(self, uri: str, data: Dict[str, Any]) -> requests.Response:
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
        """
        logger.info("post to %s, %s", uri, data)
        return self._session.post(uri, data=data)


handler = Client()


def construct_projects_bp(cfg: Config):
    """Create constructor from function to pass in config."""
    projects_bp = Blueprint(
        "projects_bp",
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    endpoint_path = cfg["BACKEND_URL"]

    @projects_bp.route("/")
    def projects_index():  # type: ignore
        """Entrypoint for the blueprint."""
        if not check_api(endpoint_path):
            return render_template("api_down.html")

        projects = get_projects(endpoint_path)
        return render_template("projects/projects.html", projects=projects)

    @projects_bp.route("/new", methods=["POST", "GET"])
    def projects_project_new():  # type: ignore
        """Create a new project."""
        if request.method == "POST":
            project = Project(
                **{
                    "name": request.form["project_name"],
                    "number": request.form["project_id"],
                    "description": request.form["project_desc"],
                    "location": request.form["project_location"],
                }
            )

            post_project(project, endpoint_path)

            return redirect(url_for("projects_bp.projects_index"))

        return render_template("projects/project_new.html")

    @projects_bp.route("/<int:project_id>")
    def projects_project(project_id: int):  # type: ignore
        """View a single project."""
        project = get_project(project_id, endpoint_path)
        if not project:
            abort(404)

        return render_template("projects/project.html", project=project)

    @projects_bp.route("/<int:project_id>/jobs/<int:job_id>")
    def projects_job(project_id: int, job_id: int):  # type: ignore
        """View a single job."""
        job = get_job(job_id, project_id, endpoint_path)
        obj_stats = job.get_object_stats()

        return render_template(
            "projects/job.html", job=job, obj_stats=obj_stats
        )

    @projects_bp.route(
        "/<int:project_id>/jobs/<int:job_id>/toggle", methods=["PUT"]
    )  # type: ignore
    def projects_job_toggle(project_id: int, job_id: int):  # type: ignore
        """Toogle job status."""
        old_status, new_status = change_job_status(
            project_id, job_id, endpoint_path
        )

        return jsonify(old_status=old_status, new_status=new_status), 201  # type: ignore

    @projects_bp.route("/<int:project_id>/jobs/new", methods=["POST", "GET"])
    def projects_job_new(project_id: int):  # type: ignore
        """Create new job inside a project."""
        project = get_project(project_id, endpoint_path)

        if request.method == "POST":
            hardcoded_path = os.path.dirname(os.path.expanduser(root_folder))
            videos = [
                hardcoded_path + "/" + path[1:-1]
                for path in request.form["tree_data"][1:-1].split(",")
            ]
            videos = [
                path if not os.path.isdir(path) else f"Folder is empty: {path}"
                for path in videos
            ]

            job = Job(
                **{
                    "name": request.form["job_name"],
                    "description": request.form["job_description"],
                    "_status": "Pending",
                    "videos": videos,
                    "location": request.form["job_location"],
                    "_objects": list(),
                }
            )

            post_res = None
            if len(request.form["tree_data"]) > 0:
                post_res = post_job(job, project_id, endpoint_path)

            if (
                isinstance(post_res, dict)
                or len(request.form["tree_data"]) == 0
            ):
                return render_template(
                    "projects/job_new.html",
                    project_name=project.get_name(),
                    post_res=post_res,
                    form_data=request.form,
                )

            return redirect(
                url_for(
                    "projects_bp.projects_job",
                    project_id=project_id,
                    job_id=int(post_res),  # type: ignore
                )
            )

        return render_template(
            "projects/job_new.html", project_name=project.get_name()  # type: ignore
        )

    @projects_bp.route("/json")
    def projects_json() -> Dict:  # type:ignore
        """Create new job inside a project."""
        data: Dict[str, Any] = path_to_dict(os.path.expanduser(root_folder))  # type: ignore

        return data

    @projects_bp.route("/<int:project_id>/jobs/<int:job_id>/csv")
    def projects_job_make_csv(project_id: int, job_id: int):  # type: ignore
        """Download results of a job as a csv-file."""
        job = get_job(job_id, project_id, endpoint_path)
        if job is None:
            return render_template("404.html"), 404

        obj_stats = job.get_object_stats()

        if not isinstance(job, Job):
            print("nei")

        # PoC of download file
        with tempfile.NamedTemporaryFile(suffix=".csv") as csv_file:

            # write headers to file
            csv_file.write(b"id,label,time_in,time_out,probability\n")

            for idx, obj in enumerate(job._objects):
                csv_file.write(
                    str.encode(
                        f"{idx},{obj.label},{obj.time_in},{obj.time_out},{obj.probability}\n"
                    )
                )

            csv_file.seek(0)

            return send_file(
                csv_file.name,
                as_attachment=True,
                mimetype="text/plain",
                attachment_filename=f"report_p{project_id}_j{job_id}.csv",
            )

    return projects_bp


def get_project(project_id: int, endpoint: str) -> Optional[Project]:
    """Get one project from endpoint.

    Parameters
    ----------
    project_id  :   int
                    Id of project to get.
    endpoint    :   str
                    API endpoint.

    Returns
    -------
    Optional[Project]
                Project from core with `project_id`.
    """
    result = handler.get(f"{endpoint}/projects/{project_id}")

    if isinstance(result, requests.Response):
        return Project.from_dict(result.json())  # type: ignore

    return None


def get_projects(endpoint: str) -> Optional[List[Project]]:
    """Get all projects from endpoint.

    Parameters
    ----------
    endpoint    :   str
                    API endpoint.

    Returns
    -------
    Optional[List[Project]]
                List of all `Project` from `core`.
    """
    result = handler.get(f"{endpoint}/projects/")

    if isinstance(result, requests.Response):
        return [Project.from_dict(p) for p in result.json()]  # type: ignore

    return None


def post_project(project: Project, endpoint: str) -> None:
    """Post project from endpoint.

    Parameters
    ----------
    project     :   Project
                    Project to send to `core` api.
    endpoint    :   str
                    API endpoint.
    """
    result = handler.post(f"{endpoint}/projects/", project.to_json())  # type: ignore

    if isinstance(result, requests.Response):
        logger.info(
            "Project %s posted with status_code: %s",
            project.id,
            result.status_code,
        )

    return None


def get_job(job_id: int, project_id: int, endpoint: str) -> Optional[Job]:
    """Get job to job."""
    try:
        r_project = requests.get(f"{endpoint}/projects/{project_id}/")  # type: ignore
        r_job = requests.get(f"{endpoint}/projects/{project_id}/jobs/{job_id}")  # type: ignore
    except requests.ConnectionError:
        logger.error("API is not running!")
        return

    if not r_project.status_code == requests.codes.ok:
        print(f"Recived an err; {r_project.status_code}")
        return

    if not r_job.status_code == requests.codes.ok:
        print(f"Recived an err; {r_job.status_code}")
        return

    return Job.from_dict(
        r_job.json(), project_id, r_project.json()["name"]  # type: ignore
    )


def post_job(job: Job, project_id: int, endpoint: str):
    """Post new job to job."""
    try:
        r = requests.post(  # type:ignore
            f"{endpoint}/projects/{project_id}/jobs", data=job.to_json()
        )
    except requests.ConnectionError:
        return "API is not running!"

    if r.status_code == requests.codes.bad_request:
        return r.json()["detail"]

    if not r.status_code == requests.codes.created:
        print(f"Recived an err; {r.status_code}")

    return r.json()["id"]


def change_job_status(
    project_id: int, job_id: int, endpoint: str
) -> Tuple[Optional[str], Optional[str]]:
    """Change job status."""
    try:
        r_project = requests.get(f"{endpoint}/projects/{project_id}/")  # type: ignore
        r_job = requests.get(f"{endpoint}/projects/{project_id}/jobs/{job_id}")  # type: ignore
    except requests.ConnectionError:
        logger.error("API is not running!")
        return None, None

    if not r_project.status_code == requests.codes.ok:
        print(f"Recived an err; {r_project.status_code}")
        return None, None  # type: ignore

    if not r_job.status_code == requests.codes.ok:
        print(f"Recived an err; {r_job.status_code}")
        return None, None  # type: ignore

    job = Job.from_dict(
        r_job.json(), project_id, r_project.json()["name"]  # type: ignore
    )

    old_status = job.get_status()

    new_status: str = ""

    if job.get_status() == "pending" or job.get_status() == "paused":
        r_post = requests.post(  # type:ignore
            f"{endpoint}/projects/{project_id}/jobs/{job_id}/start"
        )
        if r_post.status_code == requests.codes.accepted:
            new_status = "running"
        else:
            print(f"Recived an err; {r_post.status_code}")
    elif job.get_status() == "running":
        r_post = requests.post(  # type:ignore
            f"{endpoint}/projects/{project_id}/jobs/{job_id}/pause"
        )
        if r_post.status_code == requests.codes.accepted:
            new_status = "paused"
        else:
            print(f"Recived an err; {r_post.status_code}")
    else:
        new_status = "done"

    return old_status, new_status  # type: ignore


def check_api(endpoint: str) -> bool:
    """Check if API responds."""
    try:
        requests.post(f"{endpoint}")  # type: ignore
    except requests.ConnectionError:
        return False

    return True


def path_to_dict(path: str) -> Dict[str, str]:
    """Polute endpoint with stuff."""
    d = {"text": os.path.basename(path)}
    if os.path.isdir(path):
        d["children"] = [  # type: ignore
            path_to_dict(os.path.join(path, x)) for x in os.listdir(path)
        ]
    else:
        d["icon"] = "jstree-file"

    return d
