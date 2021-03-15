"""Blueprint for the projects module."""
import json
import os
from dataclasses import asdict

import requests
from flask import Blueprint, Config, redirect, render_template, request, url_for

from app.model import Detection, Project, Video


def construct_projects_bp(cfg: Config):
    """Create constructor from function to pass in config."""
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

    @projects_bp.route("/new", methods=["POST", "GET"])
    def projects_project_new():
        """Create a new project."""
        if request.method == "POST":
            project = Project(
                **{
                    "name": request.form["project_name"],
                    "number": request.form["project_id"],
                    "description": request.form["project_desc"],
                }
            )

            post_project(project, cfg["BACKEND_URL"])

            return redirect(url_for("projects_bp.projects_index"))

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

    return projects_bp


def post_project(project: Project, endpoint: str):
    """Post new project to endpoint."""
    r = requests.post(endpoint + "/projects/", data=project.to_json())

    if not r.status_code == requests.codes.ok:
        print("nei")

    return redirect(url_for("projects_bp.projects_index"))


def path_to_dict(path):
    """Polute endpoint with stuff."""
    d = {"text": os.path.basename(path)}
    if os.path.isdir(path):
        d["children"] = [
            path_to_dict(os.path.join(path, x)) for x in os.listdir(path)
        ]

    return d
