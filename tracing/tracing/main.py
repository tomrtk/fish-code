"""Entrypoint to start API."""
import argparse
import logging
from typing import Optional, Sequence

import uvicorn

from tracing import api

logger = logging.getLogger(__name__)


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Entrypoint to start API."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        type=str,
        help="IP to listen to, default 0.0.0.0",
    )
    parser.add_argument(
        "--port", default=8001, type=str, help="Bind port, default 8001"
    )
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

    args = parser.parse_args(argsv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Tracing started in debug mode")
    else:
        logging.basicConfig(level=logging.INFO)
        logger.info("Core started")

    if not args.test:
        uvicorn.run(api.tracking, host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    exit(main())
