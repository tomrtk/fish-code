"""Module containing runtime of _core_."""
import argparse
import logging
from typing import Optional, Sequence

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core import model
from core.api import core_api

# Workaround to get proper import.
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Start runtime of core module."""
    # Handle any command argument.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("--host", default="0.0.0.0", type=str, help="IP")
    parser.add_argument("--port", default="8000", type=int, help="Port")
    parser.add_argument("--test", default=False, action="store_true")
    parser.add_argument(
        "--dev", default=False, action="store_true"
    )  # No ops, needed for root-app.
    args = parser.parse_args(argsv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Core started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Core started")

    if not args.test:  # only part not tested in tests
        uvicorn.run(core_api, host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    exit(main())
