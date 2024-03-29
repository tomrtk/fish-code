"""Module containing runtime of _core_."""
import argparse
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import clear_mappers, scoped_session, sessionmaker
from sqlalchemy.orm.session import close_all_sessions

import core.api
import core.services
from config import load_config
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)

core_api = core.api.core_api  # type: ignore
config = load_config()

sessionfactory: Optional[scoped_session] = None
engine: Optional[Engine] = None


def setup(db_name: Optional[str] = None) -> None:
    """Set up database."""
    global sessionfactory, engine
    if db_name is None:
        db_file = config.get("CORE", "database_path", fallback="data.db")
        # Ensure application data folder is created
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    else:
        db_file = db_name

    logger.info("Creating database engine")
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )  # type: ignore
    # Create tables from defined schema.
    logger.info("Creating database schema")
    metadata.create_all(engine)

    # Make a scoped session to be used by other threads in processing.
    # https://docs.sqlalchemy.org/en/13/orm/contextual.html#sqlalchemy.orm.scoping.scoped_session
    sessionfactory = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine),
    )

    # Map db tables to objects.
    start_mappers()
    logger.debug("Database connected.")


def shutdown() -> None:
    """Clean up at shutdown of core."""
    close_all_sessions()
    clear_mappers()


def main(
    argsv: Optional[Sequence[str]] = None,
    db_path: Optional[str] = None,
) -> int:
    """Start runtime of core module."""
    # Handle any command argument.
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("--host", type=str, help="IP")
    parser.add_argument("--port", type=int, help="Port")
    parser.add_argument("--test", default=False, action="store_true")
    parser.add_argument(
        "--dev",
        default=False,
        action="store_true",
    )  # No ops, needed for root-app.
    args, _ = parser.parse_known_args(argsv)
    hostname = config.get("CORE", "hostname", fallback="127.0.0.1")
    port = config.getint("CORE", "port", fallback=8000)

    # Let host argument override config
    if args.host:
        logger.info(
            "Overriding core API hostname from {} to {}".format(
                config.get("CORE", "hostname"),
                args.host,
            ),
        )
        hostname = args.host

    # Let port argument override config
    if args.port:
        logger.info(
            "Overriding core API port from {} to {}".format(
                config.getint("CORE", "port"),
                args.port,
            ),
        )
        port = args.port

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Core started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Core started")

    # only part not tested in tests
    if not args.test:  # pragma: no cover
        setup(db_path)
        assert sessionfactory is not None
        core.services.start_scheduler(sessionfactory())

        uvicorn.run(
            core_api,
            host=hostname,
            port=port,
            reload=False,
            workers=1,
            access_log=False,
        )

        core.services.stop_scheduler()
        shutdown()

    return 0


if __name__ == "__main__":
    exit(main())  # pragma: no cover
