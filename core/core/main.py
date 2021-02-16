"""Module containing runtime of _core_."""
import argparse
import logging
from typing import Optional, Sequence

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core import model

# Workaround to get proper import.
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import start_mappers

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
        print("Core started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        print("Core started")

    # Testing setup of repository.
    engine = create_engine("sqlite:///data.db", echo=True)

    session_maker = sessionmaker(bind=engine)
    # start_mappers()
    # run(session_maker)

    return 0


def run(session_maker: sessionmaker) -> None:
    """Test run application."""
    logger.debug("Making repo")
    project_repo = ProjectRepository(session_maker())
    new_project = model.Project("test", "1", "test beskivelse")
    project_repo.add(new_project)
    print(project_repo.list())


if __name__ == "__main__":
    exit(main())
