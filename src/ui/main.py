"""Initilization of the application."""

import os
from typing import Any, Mapping, Optional, Tuple, Union

from flask import Flask, render_template
from werkzeug.exceptions import (
    HTTPException,
    InternalServerError,
    NotFound,
    UnprocessableEntity,
)

from ui.projects.projects import construct_projects_bp


def create_app(test_config: Optional[Mapping[str, Any]] = None) -> Flask:
    """Application factory to setup the loading of the application."""
    app = Flask(__name__)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.cfg", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    projects_bp = construct_projects_bp(app.config)

    app.register_blueprint(projects_bp, url_prefix="/projects")

    @app.route("/")
    def index() -> str:
        return render_template("index.html", msg="Gjoevik")

    @app.route("/image")
    def image() -> str:
        return render_template("image.html")

    @app.errorhandler(Exception)
    def handle_exception(
        e: HTTPException,
    ) -> Union[HTTPException, Tuple[str, int]]:
        # pass through HTTP errors
        if isinstance(e, HTTPException):
            return e

        msg = "Something has gone wrong, sorry..."
        return render_template("error.html", msg=msg, e=e), 500

    @app.errorhandler(NotFound)
    def page_not_found(e: HTTPException) -> Tuple[str, int]:
        msg = "Nothing was found here."
        return render_template("error.html", msg=msg, e=e), 404

    @app.errorhandler(UnprocessableEntity)
    def unprocessable_entity(e: HTTPException) -> Tuple[str, int]:
        msg = "Could not process request."
        return render_template("error.html", msg=msg, e=e), 422

    return app
