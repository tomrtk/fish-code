"""Small script to run the application.

Includes an option for running using livereload.  This helps out a lot
when developing.
"""

import logging
import os

import waitress
from livereload import Server  # type: ignore

import ui.main as web  # type: ignore


def serve_debug() -> None:
    """Workaround for avoiding lamdba. Starts UI in debug."""
    serve(production=False)


def serve_prod() -> None:
    """Workaround for avoiding lamdba. Starts UI in production."""
    serve(production=True)


def serve(
    production: bool = True, port: int = 5000, host: str = "0.0.0.0"
) -> None:
    """Serve the application."""
    if production:
        logger = logging.getLogger("waitress")
        logger.setLevel(logging.INFO)
        logger.info("Starting server in production")

        ui_wsgi = web.create_app().wsgi_app  # type: ignore
        waitress.serve(ui_wsgi, host=host, port=port)  # type: ignore
    else:
        ui = web.create_app()  # type: ignore

        if (
            "FLASK_LIVERELOAD" in os.environ
            and os.environ["FLASK_LIVERELOAD"] == "1"
        ):
            Server(ui.wsgi_app).serve()  # type: ignore
        else:
            ui.run(use_reloader=False)


if __name__ == "__main__":
    serve(False)
