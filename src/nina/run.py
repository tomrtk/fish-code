"""Start all sub-packages as a new prosess."""
import argparse
import logging
from collections.abc import Sequence
from multiprocessing import Process
from typing import Optional

from config import load_config
from core.main import main as core_main  # type: ignore
from detection.main import main as detection_main  # type: ignore
from tracing.main import main as tracing_main  # type: ignore
from ui.run import serve_debug, serve_prod  # type: ignore

logger = logging.getLogger(__name__)
config = load_config()


def main(argsv: Optional[Sequence[str]] = None) -> int:
    """Run all packages in parallel from root project.

    Parameters
    ----------
    argsv   :   Optional[Sequence[str]]
                Command line arguments if functions is called directly.
    """
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument(
        "--dev",
        default=False,
        action="store_true",
        help="Run web server in development mode.",
    )
    main_args, _ = main_parser.parse_known_args(argsv)
    processes: list[Process] = []

    # Let dev argument override global config parameter
    if main_args.dev:
        logger.info(
            "Overriding config and enabling development mode.",
        )  # pragma: no cover
        config["GLOBAL"]["development"] = str(main_args.dev)  # pragma: no cover

    if config.getboolean("GLOBAL", "development"):
        ui_process = Process(target=serve_debug)  # pragma: no cover
    else:
        ui_process = Process(target=serve_prod)

    ui_process.daemon = True
    processes.append(ui_process)

    core_process = Process(target=core_main)
    core_process.daemon = True
    processes.append(core_process)

    tracing_process = Process(target=tracing_main)
    tracing_process.daemon = True
    processes.append(tracing_process)

    detection_process = Process(target=detection_main)
    detection_process.daemon = True
    processes.append(detection_process)

    # Start all processes
    for p in processes:
        logger.info("Starting process %s", p.name)
        p.start()

    # Wait for processes to close
    for p in processes:
        try:
            p.join()
        except BaseException as e:
            logger.error(e)

    return 0


if __name__ == "__main__":
    exit(main())
