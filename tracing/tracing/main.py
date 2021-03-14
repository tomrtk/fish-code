"""Entrypoint to start API."""
import uvicorn

from tracing import api


def main():
    """Entrypoint to start API."""
    uvicorn.run(api.tracking, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
