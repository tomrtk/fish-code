"""Blueprint for the projects module."""
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

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
            logger.debug(request.form)
            hardcoded_path = os.path.dirname(os.path.expanduser(root_folder))
            videos = [
                hardcoded_path + "/" + path[1:-1]
                for path in request.form["tree_data"][1:-1].split(",")
            ]
            videos = [path for path in videos if os.path.isfile(path)]
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
                print("Tree")
                post_res = post_job(job, project_id, endpoint_path)

            if post_res or len(request.form["tree_data"]) == 0:
                print("post-res")
                return render_template(
                    "projects/job_new.html",
                    project_name=project.get_name(),
                    post_res=post_res,
                    form_data=request.form,
                )

            return redirect(
                url_for("projects_bp.projects_project", project_id=project_id)
            )

        return render_template(
            "projects/job_new.html", project_name=project.get_name()  # type: ignore
        )

    @projects_bp.route("/json")
    def projects_json() -> Dict:  # type:ignore
        """Create new job inside a project."""
        data: Dict[str, Any] = path_to_dict(os.path.expanduser(root_folder))  # type: ignore

        return data

    @projects_bp.route("/jobs")
    def projects_jobs():  # type: ignore
        """Route for serving a large table."""
        return render_template("projects/report/result.html")

    @projects_bp.route("/<int:project_id>/jobs/<int:job_id>/csv")
    def projects_job_make_csv(project_id: int, job_id: int):  # type: ignore
        """Download results of a job as a csv-file."""
        detections = [
            Detection(
                **{
                    "id": i,
                    "report_type": f"Type{i}",
                    "start": "Now",
                    "stop": "Later",
                    "video_path": "C:\\",
                }
            )
            for i in range(1, 100)
        ]

        # PoC of download file
        with tempfile.NamedTemporaryFile(suffix=".csv") as csv_file:

            # write headers to file
            csv_file.write(b"id,class,start,stop,video\n")

            for d in detections:
                csv_file.write(
                    str.encode(
                        f"{d.id},{d.report_type},{d.start},{d.stop}, {d.video_path}\n"
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


def get_projects(endpoint: str) -> Optional[List[Project]]:
    """Get projects from endpoint."""
    try:
        r = requests.get(f"{endpoint}/projects/")  # type: ignore
    except requests.ConnectionError:
        return "API not running!"  # type: ignore

    if not r.status_code == requests.codes.ok:
        print(f"Recived an err; {r.status_code}")

    return [Project.from_dict(p) for p in r.json()]  # type: ignore


def get_project(project_id: int, endpoint: str) -> Optional[Project]:
    """Get project from endpoint."""
    try:
        r = requests.get(f"{endpoint}/projects/{project_id}")  # type: ignore
    except requests.ConnectionError:
        return "API is not running!"  # type: ignore

    if not r.status_code == requests.codes.ok:
        print(f"Recived an err; {r.status_code}")
        return None

    return Project.from_dict(r.json())  # type: ignore


def post_project(project: Project, endpoint: str):
    """Post new project to endpoint."""
    try:
        r = requests.post(  # type: ignore
            f"{endpoint}/projects/", data=project.to_json()  # type: ignore
        )
    except requests.ConnectionError:
        return "API is not running!"

    if not r.status_code == requests.codes.ok:
        print(f"Recived an err; {r.status_code}")

    return redirect(url_for("projects_bp.projects_index"))


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

    if not r.status_code == requests.codes.ok:
        print(f"Recived an err; {r.status_code}")

    return None


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
