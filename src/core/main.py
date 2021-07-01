"""Module containing runtime of _core_."""
import argparse
import logging
from typing import Optional, Sequence

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import clear_mappers, scoped_session, sessionmaker
from sqlalchemy.orm.session import close_all_sessions

import core.api
import core.services
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)

core_api = core.api.core_api  # type: ignore

sessionfactory: Optional[scoped_session] = None
engine: Optional[Engine] = None


def setup(db_name: str = "data.db") -> None:
    """Set up database."""
    global sessionfactory, engine
    logger.info("Creating database engine")
    engine = create_engine(
        f"sqlite:///{db_name}",
        connect_args={"check_same_thread": False},
    )
    # Create tables from defined schema.
    logger.info("Creating database schema")
    metadata.create_all(engine)

    # Make a scoped session to be used by other threads in processing.
    # https://docs.sqlalchemy.org/en/13/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session
    sessionfactory = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    # Map db tables to objects.
    start_mappers()
    logger.debug("Database connected.")


def shutdown() -> None:
    """Clean up at shutdown of core."""
    close_all_sessions()
    clear_mappers()


def main(
    argsv: Optional[Sequence[str]] = None, db_path: str = "data.db"
) -> int:
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
    args, _ = parser.parse_known_args(argsv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Core started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Core started")

    if not args.test:  # only part not tested in tests
        setup(db_path)
        core.services.start_scheduler()

        uvicorn.run(
            core_api,
            host=args.host,
            port=args.port,
            reload=False,
            workers=1,
            debug=False,
            access_log=False,
        )

        core.services.stop_scheduler()
        shutdown()

    return 0


if __name__ == "__main__":
    exit(main())
