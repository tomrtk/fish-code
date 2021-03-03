"""Small script to run the application.

Includes an option for running using livereload.  This helps out a lot
when developing.
"""

import argparse
import os
from typing import Optional, Sequence

from livereload import Server

import app.app as web


def serve():
    """Serve the application."""
    app = web.create_app()

    if (
        "FLASK_LIVERELOAD" in os.environ
        and os.environ["FLASK_LIVERELOAD"] == "1"
    ):
        Server(app.wsgi_app).serve()
    else:
        app.run()


if __name__ == "__main__":
    serve()
