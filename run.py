import logging
from multiprocessing import Process
from typing import List

from app.app import create_app

from core.main import main as core_main
from tracing.main import main as tracing_main

logger = logging.getLogger(__name__)


def main() -> int:
    """Run all packages in parallel from root project."""

    processes: List[Process] = list()

    core_process = Process(target=core_main, args=(None,))
    core_process.daemon = True
    processes.append(core_process)

    tracing_process = Process(target=tracing_main, args=())
    tracing_process.daemon = True
    processes.append(tracing_process)

    ui_main = create_app()
    ui_process = Process(target=ui_main.run, args=())
    ui_process.daemon = True
    processes.append(ui_process)

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
