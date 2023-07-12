"""Module defining main runtime for detection package."""
import argparse
import logging
from collections.abc import Sequence
from typing import Optional

import uvicorn  # type: ignore

from config import load_config
from detection.api import detection_api

logger = logging.getLogger(__name__)
config = load_config()


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Start runtime of detection module."""
    # Handle any command argument.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Run with debug logging.",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="IP-adresse, defaults to `0.0.0.0`.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port for API to run on, defaults to `8003`.",
    )
    parser.add_argument(
        "--test",
        default=False,
        action="store_true",
        help="Used for testing only. API will not start.",
    )
    args, _ = parser.parse_known_args(argsv)
    hostname = config.get("DETECTION", "hostname", fallback="127.0.0.1")
    port = config.getint("DETECTION", "port", fallback=8003)

    # Let host argument override config
    if args.host:
        logger.info(
            "Overriding detection API hostname from {} to {}".format(
                config.get("DETECTION", "hostname"),
                args.host,
            ),
        )
        hostname = args.host

    # Let port argument override config
    if args.port:
        logger.info(
            "Overriding detection API port from {} to {}".format(
                config.getint("DETECTION", "port"),
                args.port,
            ),
        )
        port = args.port

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Detection started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Detection started")

    # only part not tested in tests
    if not args.test:  # pragma: no cover
        uvicorn.run(
            detection_api,
            host=hostname,
            port=port,
        )

    return 0


if __name__ == "__main__":
    exit(main())
