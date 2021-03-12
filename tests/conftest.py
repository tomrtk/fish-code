import pytest

from tracing.main import main as tracing_main  # type: ignore
from multiprocessing import Process
import time
import requests


@pytest.fixture
def tracing_api():
    """Start tracing API.

    Makes sure that the API is running via `check_api()`

    See Also
    --------
    check_api()
    """
    tracing_process = Process(target=tracing_main)
    tracing_process.start()
    check_api(host="localhost", port="8001")
    yield
    tracing_process.terminate()


def check_api(max_tries: int = 4, host: str = "localhost", port: str = "8000"):
    """check if an endpoint is reachable.

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
