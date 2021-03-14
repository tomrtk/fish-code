"""Blueprint for the projects module."""
import json
import os

from flask import Blueprint, redirect, render_template, request, url_for

from app.model import Detection, Video

projects_bp = Blueprint(
    "projects_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@projects_bp.route("/")
def projects_index():
    """Entrypoint for the blueprint."""
    return render_template("projects/index.html")


@projects_bp.route("/new")
def projects_project_new():
    """Create a new project."""
    return render_template("projects/project_new.html")


@projects_bp.route("/<int:project_id>")
def projects_project(project_id: int):
    """View a single project."""
    return render_template("projects/project.html")


@projects_bp.route("/<int:project_id>/jobs/<int:job_id>")
def projects_job(project_id: int, job_id: int):
    """View a single job."""
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
    videos = [
        Video(
            **{
                "id": i,
                "location": f"Test{i}",
                "status": "{status}".format(
                    status="Pendig" if (i % 2) == 0 else "Ferdig"
                ),
                "video_path": f"C:\\Filmer\\Film_{i*2}",
            }
        )
        for i in range(1, 101)
    ]

    return render_template(
        "projects/job.html", detections=detections, videos=videos
    )


def path_to_dict(path):
    """Polute endpoint with stuff."""
    d = {"text": os.path.basename(path)}
    if os.path.isdir(path):
        d["type"] = "directory"
        d["children"] = [
            path_to_dict(os.path.join(path, x)) for x in os.listdir(path)
        ]
    else:
        d["type"] = "file"
    return d


@projects_bp.route("/<int:project_id>/jobs/new", methods=["POST", "GET"])
def projects_job_new(project_id: int):
    """Create new job inside a project."""
    data = path_to_dict("/Users/mt/Downloads")

    if request.method == "POST":
        print(request.form)
        return redirect(
            url_for("projects_bp.projects_project", project_id=project_id)
        )

    return render_template(
        "projects/job_new.html",
    )


@projects_bp.route("/json")
def projects_json():
    """Create new job inside a project."""
    data = path_to_dict("/Users/mt/Downloads")

    return data


@projects_bp.route("/jobs")
def projects_jobs():
    """Route for serving a large table."""
    return render_template("projects/report/result.html")
