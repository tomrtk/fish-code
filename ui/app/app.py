import os

from flask import Flask, render_template

from app.model import *
from app.projects.projects import projects_bp


def create_app(test_config=None):  # type: ignore
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(  # type: ignore
        SECRET_KEY="dev",
        BACKEND_URL="http://127.0.0.1:9955",
    )

    # app.config["TEMPLATES_AUTO_RELOAD"] = True

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)  # type: ignore
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)  # type: ignore

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.register_blueprint(projects_bp, url_prefix="/projects")

    @app.route("/")
    def index():  # type: ignore
        return render_template("index.html", msg="Gjoevik")

    @app.route("/report")
    def report_page():  # type: ignore
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

        return render_template("report/result.html", detections=detections)

    @app.route("/image")
    def image():  # type: ignore
        return render_template("image.html")

    @app.errorhandler(500)
    def handle_exception(e):  # type: ignore
        return "This page does not exist", 500

    return app
