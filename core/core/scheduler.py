"""Scheduler class to orchestrate processing of jobs."""
import asyncio
import logging
import random

logger = logging.getLogger(__name__)


async def process_job(queue):
    """Process a job."""
    while True:
        logger.info("worker created, awaiting job")
        job: str = await queue.get()

        logger.info("Starting job")

        await asyncio.sleep(random.uniform(0.05, 2))
        print(job)


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
        self.queue = asyncio.Queue()

    async def put_job(self, job: str):
        """Put a job into the scheduling queue."""
        logger.info("putting job in queue")
        await self.queue.put(job)

    async def spawn_processes(self):
        """Spawns child processes for jobs in the queue."""
        for i in range(10):
            print("doing stuff")

    async def complete_job(self):
        """Complete a job."""
        pass
