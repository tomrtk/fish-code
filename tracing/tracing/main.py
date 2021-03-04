"""Entrypoint to start API."""
import uvicorn

from . import api


def main():
    """Entrypoint to start API."""
    uvicorn.run(api.tracking, host="0.0.0.0", port=8001)
