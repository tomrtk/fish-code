"""Initilization of the application."""

import os

from flask import Flask, render_template

from ui.projects.projects import construct_projects_bp


def create_app(test_config=None):  # type: ignore
    """Application factory to setup the loading of the application."""
    app = Flask(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.cfg", silent=True)  # type: ignore
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)  # type: ignore

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    projects_bp = construct_projects_bp(app.config)

    app.register_blueprint(projects_bp, url_prefix="/projects")

    @app.route("/")
    def index():  # type: ignore
        return render_template("index.html", msg="Gjoevik")

    @app.route("/image")
    def image():  # type: ignore
        return render_template("image.html")

    @app.errorhandler(500)
    def handle_exception(e):  # type: ignore
        return "This page does not exist", 500

    @app.errorhandler(404)
    def page_not_found(e):  # type:ignore
        return render_template("404.html"), 404

    return app
