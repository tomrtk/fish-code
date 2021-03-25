"""Scheduler class to orchestrate processing of jobs."""
import asyncio
import logging
import multiprocessing
import random
import time

from core.model import Job
from core.services import process_job

logger = logging.getLogger(__name__)


class Worker(multiprocessing.Process):
    """Worker to process a job."""

    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        """Worker thread core loop."""
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                logger.info(f"Process {self.name} exiting, no more work to do.")
                self.task_queue.task_done()
                break
            elif isinstance(next_task, Job):
                logger.info(
                    f"Process {self.name} received job '{next_task.name}'"
                )
                processed_job = process_job(next_task)
                self.result_queue.put(processed_job)
        return


class Singleton(type):
    """Singleton class definition, there can only be one instance."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Ensure there is only once instance, and same instance returned if created."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class Scheduler(metaclass=Singleton):
    """Scheduler class to control processing of jobs."""

    def __init__(self) -> None:
        self.tasks = multiprocessing.JoinableQueue()
        self.results = multiprocessing.Queue()

        logger.info("Creating 2 job workers")
        workers = [Worker(self.tasks, self.results) for i in range(2)]
        for w in workers:
            w.start()

    async def put_job(self, job: str):
        """Put a job into the scheduling queue."""
        logger.info("putting job in queue")
        self.tasks.put(job)
