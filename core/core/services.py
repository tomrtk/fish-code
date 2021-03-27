"""Services used in this application."""
import logging
import multiprocessing
import threading
from typing import List, Tuple

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers, sessionmaker

from core.interface import Detector, to_track
from core.model import Job, Video
from core.repository import SqlAlchemyProjectRepository as ProjectRepository
from core.repository.orm import metadata, start_mappers

logger = logging.getLogger(__name__)

job_queue = multiprocessing.JoinableQueue()


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


def process_job(project_id: int, job_id: int):
    """Process all videos in a job and finds objects."""
    # Setup of runtime stuff. Should be moved to its own place later.
    engine = create_engine(
        "sqlite:///data.db",
        connect_args={"check_same_thread": False},
    )
    # Create tables from defines schema.
    metadata.create_all(engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    start_mappers()

    repo = ProjectRepository(session())
    project = repo.get(project_id)

    if not project:
        logger.warning(f"Could not get project {project_id}.")
        return

    job = project.get_job(job_id)

    if not job:
        logger.warning(f"Could not get job {job_id} in project {project_id}.")
        return

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
    clear_mappers()

    return job


def schedule():
    """Scheduler function, gets run by the scheduler thread."""
    logger.info("Scheduler started.")
    while True:
        next_task = job_queue.get()
        if next_task is None:
            break
        elif isinstance(next_task, Tuple):
            # TODO: This means a new job has been added.
            process_job(next_task[0], next_task[1])
        job_queue.task_done()
    logger.info(f"scheduler ending.")


schedule_thread = threading.Thread(target=schedule)


def stop_scheduler():
    """Stop the scheduler thread."""
    # TODO: Should have a timeout that api handles if it does not get picked up.
    # For example when scheduler is not running.
    job_queue.put(None)


def start_scheduler():
    """Start the scheduler thread."""
    try:
        schedule_thread.start()
    except RuntimeError:
        logger.error("Scheduler process is already started.")


def queue_job(project_id: int, job_id: int):
    """Enqueue a job."""
    logger.info(f"Job {job_id} in project {project_id} scheduled to run")
    job_queue.put((project_id, job_id))
