"""Module containing runtime of _core_."""
import argparse
import logging
from typing import Optional, Sequence

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core import model

# Workaround to get proper import.
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Start runtime of core module."""
    # Handle any command argument.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true")
    args = parser.parse_args(argsv)

    # Temporary use of arguments.
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Core started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logging.info("Core started")

    return 0


if __name__ == "__main__":
    exit(main())
