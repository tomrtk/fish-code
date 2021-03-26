"""Services used in this application."""
import logging
import multiprocessing
from datetime import datetime
from typing import List

import numpy as np

from core.interface import Detector, to_track
from core.model import Job, Video

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
                self.task_queue.task_done()
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

    async def put_job(self, job: Job):
        """Put a job into the scheduling queue."""
        logger.info(f"putting job {job.name} in queue")
        self.tasks.put(job)


scheduler = Scheduler()


class VideoLoader:
    """Utility class to abstract away video files and turn them into an iterator of frames."""

    def __init__(self, videos: List[Video], batchsize: int = 25) -> None:
        self.videos = videos
        self.frames = sum([v.frames for v in self.videos])
        self.batchsize = batchsize

    def __len__(self) -> int:
        """Get total sum of frames in all video files."""
        return self.frames

    def __iter__(self):
        """Iterate all frames in videos in a set batch size.

        Return
        ------
        np.array    :
            Numpy array containing `batchsize` amount of frames. Gets frames from
            all videos seemlessly.
        """
        batch = []
        timestamps = []
        for video in self.videos:
            assert isinstance(video, Video), "VideoLoaded only support Video"
            for n, frame in enumerate(video):
                batch.append(frame)
                timestamps.append(video.timestamp_at(n))
                if len(batch) == self.batchsize:
                    yield np.array(batch), timestamps
                    batch = []
                    timestamps = []

        if len(batch) > 0:
            yield np.array(batch), timestamps


def process_job(job: Job) -> Job:
    """Process all videos in a job and finds objects."""
    # make sure its sorted before we start
    job.videos.sort(key=lambda x: x.timestamp.timestamp())

    batchsize: int = 50

    video_loader = VideoLoader(job.videos, batchsize=batchsize)
    det = Detector()

    all_frames = []
    for batchnr, (batch, timestamp) in enumerate(video_loader):
        assert isinstance(batch, np.ndarray), "Batch must be of type np.ndarray"
        frames = det.predict(batch, "fishy")

        # Iterate over all frames to set timestamps
        for n, frame in enumerate(frames):
            abs_frame_nr = batchnr * batchsize + n

            frame.timestamp = timestamp[n]

            # Adds the absolute frame number to the frame before tracking.
            # This help popuplate the timestamp for objects.
            frame.detections = [
                dets.set_frame(abs_frame_nr) for dets in frame.detections
            ]
            frame.idx = abs_frame_nr
            all_frames.append(frame)

    objects = to_track(all_frames)

    for obj in objects:
        job.add_object(obj)

    job.complete()

    return job
