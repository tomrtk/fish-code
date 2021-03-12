"""Configure pytest."""
import logging
import os

logger = logging.getLogger(__name__)


def pytest_configure():
    """Configure pytest before it starts running tests."""
    # Clean up test.db file from previous tests if it exists
    if os.path.exists("test.db"):
        os.remove("test.db")
        logger.info("Cleared test.db before running tests.")
    else:
        logger.info("Cannot find test.db file, ignoring.")
