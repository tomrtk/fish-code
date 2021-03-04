"""Entrypoint to start API."""
from . import api


import uvicorn


def main():
    """Entrypoint to start API."""
    uvicorn.run(api.tracking, host="0.0.0.0", port=8001)
