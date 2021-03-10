"""Small script to run the application.

Includes an option for running using livereload.  This helps out a lot
when developing.
"""

import logging
import os

import waitress
from livereload import Server

import app.app as web

logger = logging.getLogger(__name__)


def serve(
    production: bool = True, port: int = 5000, host: str = "0.0.0.0"
) -> None:
    """Serve the application."""
    if production:
        ui_wsgi = web.create_app().wsgi_app
        logger.setLevel(logging.INFO)
        logger.info("Starting server in production")
        waitress.serve(ui_wsgi, host=host, port=port)
    else:

        app = web.create_app()

        if (
            "FLASK_LIVERELOAD" in os.environ
            and os.environ["FLASK_LIVERELOAD"] == "1"
        ):
            Server(app.wsgi_app).serve()
        else:
            app.run()


if __name__ == "__main__":
    serve(False)
