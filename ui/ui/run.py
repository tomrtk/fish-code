"""Small script to run the application.

Includes an option for running using livereload.  This helps out a lot
when developing.
"""


import logging
import os

import waitress

import ui.main as web  # type: ignore


def serve_debug() -> None:
    """Workaround for avoiding lamdba. Starts UI in debug."""
    serve(production=False)


def serve_prod() -> None:
    """Workaround for avoiding lamdba. Starts UI in production."""
    serve(production=False)


def serve(
    production: bool = True, port: int = 5000, host: str = "0.0.0.0"
) -> None:
    """Serve the application."""
    if production:
        logger = logging.getLogger("waitress")
        logger.setLevel(logging.INFO)
        logger.info("Starting server in production")

        ui_server = web.create_app()
        ui_server.debug = True

        waitress.serve(ui_server.wsgi_app, host=host, port=port)  # type: ignore
    else:
        ui_server = web.create_app()  # type: ignore
        ui_server.debug = True

        ui_server.run(use_reloader=False)


if __name__ == "__main__":
    serve(False)
