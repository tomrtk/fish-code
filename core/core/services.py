"""Services used in this application."""
import logging
import math
import threading
import time
from queue import Empty, Queue
from typing import List, Tuple, Union

import numpy as np
from sqlalchemy.orm import Session

from core import api
from core.interface import Detector, to_track
from core.model import JobStatusException, Status, Video
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

    @property
    def _total_batches(self) -> int:
        """Get total batches in this video loader."""
        return math.ceil(self.frames / self.batchsize)

    def _video_for_frame(self, frame: int) -> Tuple[int, int]:
        """Find the video belonging to an absolute frame number, along with start position."""
        curframe = 0
        logger.info(f"Finding video for frame {frame}")
        for vid in self.videos:
            if curframe + vid.frames >= frame:
                return self.videos.index(vid), frame - curframe
            curframe += vid.frames
        raise IndexError(f"Cannot find video index of frame {frame}.")

    def generate_batches(self, start_batch: int = 0):
        """Generate batches from list of videos, with optional batch offset."""
        if start_batch > self._total_batches:
            raise IndexError(
                f"Start batch index {start_batch} is too big, total videos are {len(self.videos)}."
            )

        start_frame = self.batchsize * start_batch
        logger.debug(f"Absolute frame number is {start_frame}")
        start_vid, start_frame = self._video_for_frame(start_frame)
        logger.debug(f"start_vid is {start_vid}")
        logger.debug(f"start_frame is {start_frame}")

        batch = []
        timestamps = []
        current_batch = start_batch
        for vid in self.videos[start_vid:]:
            if start_frame > vid.frames:
                raise IndexError(
                    f"Start frame of {start_frame} is too big, total frame in video is {vid.frames}."
                )
            for n, frame in enumerate(vid[start_frame:]):
                batch.append(frame)
                timestamps.append(vid.timestamp_at(n + start_frame))
                if len(batch) == self.batchsize:
                    logger.info(f"Yeilding batch {current_batch}...")
                    yield current_batch, (np.array(batch), timestamps)
                    logger.info(f"Batch {current_batch} complete")
                    current_batch += 1
                    batch = []
                    timestamps = []

            start_frame = 0
            vid.vidcap_release()

        if len(batch) > 0:
            yield current_batch, (np.array(batch), timestamps)


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
    if job.status() == Status.QUEUED:
        job.start()
        repo.save()
    elif job.status() == Status.RUNNING:
        logger.warning("Job is already marked started, resuming.")
    else:
        logger.error(
            "Job must either be of status queued or running to start processing."
        )
        return

    # make sure its sorted before we start
    job.videos.sort(key=lambda x: x.timestamp.timestamp())

    batchsize: int = 50

    video_loader = VideoLoader(job.videos, batchsize=batchsize)
    det = Detector()

    if job.next_batch >= video_loader._total_batches:
        logger.warning("Job has already processed all batches in video loader.")
        job.complete()
        repo.save()
        return

    all_frames = []
    for batchnr, (batch, timestamp) in video_loader.generate_batches(
        start_batch=job.next_batch
    ):
        assert isinstance(batch, np.ndarray), "Batch must be of type np.ndarray"
        assert isinstance(batchnr, int), "Batch number must be int"

        logger.info(f"Now detecting batch {batchnr}...")
        frames = det.predict(batch, "fishy")
        logger.info(f"Finished detecting batch {batchnr}.")

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

        # store detections
        # TODO

        job.next_batch = batchnr + 1
        repo.save()

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
        if job.status() != Status.RUNNING:
            job.queue()
    except JobStatusException:
        logger.error(
            "Cannot queue job %s, it's already pending or completed.", job_id
        )
        return
    repo.save()

    logger.info(f"Job {job_id} in project {project_id} scheduled to run.")
    job_queue.put((project_id, job_id))
