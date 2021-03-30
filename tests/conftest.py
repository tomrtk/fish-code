"""Pytest fixtures used in tests."""
import pytest

from tracing.main import main as tracing_main  # type: ignore
from detection.main import main as detection_main
from core.main import main as core_main
from multiprocessing import Process
import time
import requests
import logging


@pytest.fixture
def tracing_api():
    """Start tracing API.

    Makes sure that the API is running via `check_api()`

    See Also
    --------
    check_api()
    """
    tracing_process = Process(target=tracing_main, args=(None,))
    tracing_process.start()
    check_api(host="localhost", port="8001")
    yield
    tracing_process.terminate()


logger = logging.getLogger(__name__)


@pytest.fixture
def start_core():
    """Start core API.

    NOTE: Uses the production database.

    Makes sure that the API is running via `check_api()`

    See Also
    --------
    check_api()
    """
    process = Process(target=core_main, args=(None,))
    process.start()
    logger.warning("Process started")
    check_api(max_tries=5, host="localhost", port="8000")
    yield
    process.terminate()


def check_api(
    max_tries: int = 4,
    host: str = "localhost",
    port: str = "8000",
):
    """Check if an endpoint is reachable.

    Sleeps for 2 seconds if unreachable.

    Parameter
    ---------
    max_tries: int
        Amount of retries before exiting
    host: str
        IP or hostname of endpoint
    port: str
        Port of endpoint
    """
    max_try = max_tries

    def ping(host: str, port: str):
        """Try to get from API."""
        try:
            requests.get(f"http://{host}:{port}/")
            return True
        except:
            return False

    while (not ping(host, port)) and max_try:
        max_try -= 1
        print("waiting for api")
        time.sleep(2)

    # Asserts false if endpoint is unreachable
    assert ping(host, port)


@pytest.fixture
def detection_api():
    """Start detection API.

    Makes sure that the API is running via `check_api()`

    See Also
    --------
    check_api()
    """
    detection_process = Process(target=detection_main, args=(None,))
    detection_process.start()
    check_api(max_tries=60, host="localhost", port="8003")
    yield
    detection_process.terminate()
