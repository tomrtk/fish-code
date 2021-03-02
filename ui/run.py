import argparse
import os
from typing import Optional, Sequence

from livereload import Server

import app.app as web


def create_livereload_wrapper(app):
    return Server(app.wsgi_app)


def serve():
    app = web.create_app()

    if (
        "FLASK_LIVERELOAD" in os.environ
        and os.environ["FLASK_LIVERELOAD"] == "1"
    ):
        server = create_livereload_wrapper(app)
        server.serve()
    else:
        app.run()


if __name__ == "__main__":
    serve()
