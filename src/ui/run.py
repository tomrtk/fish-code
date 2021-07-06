"""Small script to run the application.

Includes an option for running using livereload.  This helps out a lot
when developing.
"""
import logging

import waitress

import ui.main as web  # type: ignore
from config import load_config

logger = logging.getLogger(__name__)
config = load_config()


def serve_debug() -> int:
    """Workaround for avoiding lamdba. Starts UI in debug."""
    ui_server = web.create_app()  # type: ignore
    ui_server.debug = True

    ui_server.run(use_reloader=False)
    return 0


def serve_prod() -> int:
    """Workaround for avoiding lamdba. Starts UI in production."""
    logger = logging.getLogger("waitress")
    host = config.get("UI", "hostname")
    port = config.getint("UI", "port")
    logger.setLevel(logging.INFO)
    logger.info("Starting server in production")

    ui_server = web.create_app()
    ui_server.debug = False

    waitress.serve(ui_server.wsgi_app, host=host, port=port)  # type: ignore
    return 0


if __name__ == "__main__":
    exit(serve_debug())
