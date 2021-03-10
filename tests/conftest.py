import pytest

from tracing.main import main as tracing_main  # type: ignore
from multiprocessing import Process
import time


@pytest.fixture
def tracing_api():
    """Start tracing API.

    Waits three seconds before yielding to ensure the process has initialized
    """
    tracing_process = Process(target=tracing_main)
    tracing_process.start()
    time.sleep(3)
    yield
    tracing_process.terminate()
