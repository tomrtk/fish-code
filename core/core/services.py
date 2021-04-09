"""Services used in this application."""
import logging
import threading
import time
from queue import Empty, Queue
from typing import List

import numpy as np
from sqlalchemy.orm import Session

from core import api
from core.interface import Detector, to_track
from core.model import JobStatusException, Video
from core.repository import SqlAlchemyProjectRepository as ProjectRepository

logger = logging.getLogger(__name__)

job_queue: Queue = Queue()


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


def process_job(project_id: int, job_id: int, session: Session):
    """Process all videos in a job and find objects.

    Parameters
    ----------
    project_id  :   int
        Project id of the porject to start processing.
    job_id      :   int
        Job id of the job to start processing.
    """
    repo = ProjectRepository(session)
    project = repo.get(project_id)

    if not project:
        logger.warning(f"Could not get project {project_id}.")
        return

    job = project.get_job(job_id)

    if not job:
        logger.warning(f"Could not get job {job_id} in project {project_id}.")
        return

    # TODO: Send status of job back to the API
    try:
        job.start()
    except JobStatusException:
        logger.error(
            "Cannot start job %s, it's already running or completed.", job_id
        )
        return
    repo.save()

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

    repo.save()

    return job


class SchedulerThread(threading.Thread):
    """Wrapper class around Thread to handle exceptions in thread."""

    def run(self):
        """Wrap method around target function to catch exception.

        Called when `.start` is called on `Thread`.
        """
        self.exc = None
        self.ret = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)  # type: ignore
        except BaseException as e:
            self.exc = e

    def join(self):
        """Wrap method around `Thread` join to propagate exception."""
        super(SchedulerThread, self).join()
        if self.exc:
            raise RuntimeError("Exception in thread") from self.exc
        return self.ret


def schedule(event: threading.Event):
    """Scheduler function, gets run by the scheduler thread."""
    logger.info("Scheduler started.")
    while event.is_set():
        try:
            next_task = job_queue.get(timeout=1)
        except Empty:
            continue  # timeout, check if event is set.

        logger.info(
            "processing job %s from project %s", next_task[1], next_task[0]
        )

        if isinstance(next_task, tuple):
            session = api.sessionfactory()

            process_job(next_task[0], next_task[1], session=session)

        job_queue.task_done()
    logger.info(f"Scheduler ending.")


# Threes signalling event to stop.
schedule_event = threading.Event()
schedule_event.set()
# Defining scheduler thread
schedule_thread = SchedulerThread(
    target=schedule, args=(schedule_event,), daemon=True
)


def stop_scheduler():
    """Stop the scheduler thread."""
    logger.info("Stopping")

    # Clear queue, TODO Store jobs in queue and handle running jobs.
    # job_queue.queue.clear()

    # signal scheduler_thread to close.
    schedule_event.clear()

    # wait for thread to close. At most 1s if not processing a job.
    schedule_thread.join()
    logger.info("Stopped")


def start_scheduler():
    """Start the scheduler thread."""
    if not schedule_thread.is_alive():  # type: ignore
        try:
            logger.info("Starting scheduler")
            schedule_event.set()
            schedule_thread.start()

        except RuntimeError as e:
            logger.error("Scheduler could not be started", e.args)
            raise RuntimeError("Scheduler start error") from e

        logger.info("Scheduler started, %s", schedule_thread.name)
    else:
        logger.error("Scheduler is already running")


def queue_job(project_id: int, job_id: int, session: Session):
    """Enqueue a job in the scheduler.

    Parameters
    ----------
    project_id  :   int
        Project id of the porject to start processing.
    job_id      :   int
        Job id of the job to start processing.
    """
    repo = ProjectRepository(session)
    project = repo.get(project_id)

    if not project:
        logger.warning(f"Could not get project {project_id}.")
        return

    job = project.get_job(job_id)

    if not job:
        logger.warning(f"Could not get job {job_id} in project {project_id}.")
        return

    # TODO: Send status of job back to the API
    try:
        job.queue()
    except JobStatusException:
        logger.error(
            "Cannot queue job %s, it's already pending or completed.", job_id
        )
        return
    repo.save()

    logger.info(f"Job {job_id} in project {project_id} scheduled to run.")
    job_queue.put((project_id, job_id))
