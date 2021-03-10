import argparse
import logging
from multiprocessing import Process
from typing import List, Optional, Sequence

from app.run import serve

from core.main import main as core_main  # type: ignore
from tracing.main import main as tracing_main  # type: ignore

logger = logging.getLogger(__name__)


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
    main_args = main_parser.parse_args(argsv)
    processes: List[Process] = list()

    if not main_args.dev:
        ui_main = lambda: serve()
        ui_process = Process(target=ui_main)
        ui_process.daemon = True
        processes.append(ui_process)
    else:
        ui_main = lambda: serve(production=False)
        ui_process = Process(target=ui_main)
        ui_process.daemon = True
        processes.append(ui_process)

    core_process = Process(target=core_main)
    core_process.daemon = True
    processes.append(core_process)

    tracing_process = Process(target=tracing_main)
    tracing_process.daemon = True
    processes.append(tracing_process)

    # Start all processes
    for p in processes:
        logger.info("Starting process %s", p.name)
        p.start()

    # Wait for processes to close
    for p in processes:
        p.join()

    return 0


if __name__ == "__main__":
    exit(main())
