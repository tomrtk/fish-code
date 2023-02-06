"""Entrypoint to start API."""
import argparse
import logging
from collections.abc import Sequence
from typing import Optional

import uvicorn

from config import load_config
from tracing import api

logger = logging.getLogger(__name__)
config = load_config()


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Entrypoint to start API."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=str,
        help="IP to listen to.",
    )
    parser.add_argument("--port", type=int, help="Bind port.")
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Run with debug logging",
    )
    parser.add_argument(
        "--test",
        default=False,
        action="store_true",
        help="Used for testing only. API will not start.",
    )

    args, _ = parser.parse_known_args(argsv)
    hostname = config.get("TRACING", "hostname", fallback="127.0.0.1")
    port = config.getint("TRACING", "port", fallback=8001)

    # Let host argument override config
    if args.host:
        logger.info(
            "Overriding tracing API hostname from {} to {}".format(
                config.get("TRACING", "hostname"), args.host
            )
        )
        hostname = args.host

    # Let port argument override config
    if args.port:
        logger.info(
            "Overriding tracing API port from {} to {}".format(
                config.getint("TRACING", "port"), args.port
            )
        )
        port = args.port

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Tracing started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Tracing started")

    # only part not tested in tests
    if not args.test:  # pragma: no cover
        uvicorn.run(
            api.tracking,
            host=hostname,
            port=port,
        )

    return 0


if __name__ == "__main__":
    exit(main())
