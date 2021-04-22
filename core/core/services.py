"""Services used in this application."""
import logging
import math
import threading
import time
from queue import Empty, Queue
from typing import Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from core import api
from core.interface import Detector, to_track
from core.model import Frame, JobStatusException, Status, Video
from core.repository import SqlAlchemyProjectRepository as ProjectRepository

logger = logging.getLogger(__name__)

job_queue: Queue = Queue()


class VideoLoader:
    """Utility class to abstract away video files and turn them into an iterator of frames."""

    def __init__(self, videos: List[Video], batchsize: int = 25) -> None:
        self.videos = videos
        self.frames = sum([v.frame_count for v in self.videos])
        self.batchsize = batchsize

    def __len__(self) -> int:
        """Get total sum of frames in all video files.

        Return
        ------
        int     :
            Number of frames in total over all videos.
        """
        return self.frames

    @property
    def _total_batches(self) -> int:
        """Get total batches in this video loader.

        Return
        ------
        int     :
            Number of batches in total over all videos.
        """
        return math.ceil(self.frames / self.batchsize)

    def _video_for_frame(self, frame: int) -> Tuple[int, int]:
        """Find the video belonging to an absolute frame number, along with start position.

        Parameter
        ---------
        frame   :   int
            Absolute frame number over all videos in this video loader.

        Return
        ------
        (int, int)  :
            Tuple of index of video, along with local frame offset in indexed video.

        Raises
        ------
        IndexError
            When wanted frame is outside of total number of frames in a videoloader.
        IndexError
            If calculated start_frame is larger than the current video's total frame count.
        """
        curframe = 0
        logger.info(f"Finding video for frame {frame}")
        for vid in self.videos:
            if curframe + vid.frame_count >= frame:
                return self.videos.index(vid), frame - curframe
            curframe += vid.frame_count
        raise IndexError(f"Cannot find video index of frame {frame}.")

    def generate_batches(self, batch_index: int = 0):
        """Generate batches from list of videos, with optional batch offset.

        Parameter
        ---------
        batch_index :   int
            Batch number to start from.

        Yields
        ------
        batchnr, (batch, timestamps)    :   int, (np.ndarray, list)
            Yields batch along with absolute batch number and associated timestamps.

        Raises
        ------
        IndexError
            If start_batch parameter is larger than total batches in this VideoLoader
        """
        if batch_index > self._total_batches:
            raise IndexError(
                f"Start batch index {batch_index} is too big, total videos are {len(self.videos)}."
            )

        start_frame = self.batchsize * batch_index
        logger.debug(f"Absolute frame number is {start_frame}")
        start_vid, start_frame = self._video_for_frame(start_frame)
        logger.debug(f"start_vid is {start_vid}")
        logger.debug(f"start_frame is {start_frame}")

        batch = []
        timestamps = []
        framenumbers = []
        video_for_frame: Dict[int, Video] = dict()
        current_batch = batch_index
        batch_start_time = time.time()
        for vid in self.videos[start_vid:]:
            if start_frame > vid.frame_count:
                raise IndexError(
                    f"Start frame of {start_frame} is too big, total frame in video is {vid.frame_count}."
                )
            for n, frame in enumerate(vid[start_frame:]):
                batch.append(frame)
                timestamps.append(vid.timestamp_at(n + start_frame))
                framenumbers.append(n + start_frame)
                video_for_frame[n + start_frame] = vid
                if len(batch) == self.batchsize:
                    progress = round(
                        ((current_batch + 1) / self._total_batches) * 100
                    )

                    yield current_batch, (
                        progress,
                        np.array(batch),
                        timestamps,
                        video_for_frame,
                        framenumbers,
                    )

                    logger.info(
                        "Batch {} out of {} completed in {}s, job {}% complete".format(
                            current_batch,
                            self._total_batches,
                            round(time.time() - batch_start_time, 2),
                            progress,
                        )
                    )
                    batch_start_time = time.time()
                    current_batch += 1
                    batch = []
                    timestamps = []
                    framenumbers = []
                    video_for_frame = dict()

            start_frame = 0

        if len(batch) > 0:
            yield current_batch, (
                100,
                np.array(batch),
                timestamps,
                video_for_frame,
                framenumbers,
            )


def process_job(
    project_id: int, job_id: int, event: threading.Event, session: Session
):
    """Process all videos in a job and find objects.

    Parameters
    ----------
    project_id  :   int
        Project id of the porject to start processing.
    job_id      :   int
        Job id of the job to start processing.
    session     :   sqlalchemy.session
        SQLAlchemy session for this process.
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

    # Update job status
    if event.is_set():
        if job.status() is Status.QUEUED:
            job.start()
            repo.save()
        elif job.status() is Status.PAUSED:
            job.start()
            repo.save()
        elif job.status() is Status.RUNNING:
            logger.warning("Job is already marked started, resuming.")
        else:
            logger.error(
                "Job must either be of status queued, paused or running to start processing."
            )
            return
    else:
        logger.info(
            "Job processing aborted, not updating job status to running."
        )
        return

    # make sure its sorted before we start
    job.videos.sort(key=lambda x: x.timestamp.timestamp())

    batchsize: int = 50

    all_frames = []
    video_loader = VideoLoader(job.videos, batchsize=batchsize)
    det = Detector()

    # Check if job has already processed all batches
    if job.next_batch >= video_loader._total_batches:
        logger.warning("Job has already processed all batches in video loader.")
        job.complete()
        repo.save()
        return
    else:
        # TODO: Should get all previously detected Frames/Detections from repo
        pass

    # Populate all_frames variable with previously detected frames.
    for vid in job.videos:
        vid.is_processed()
        for frame in vid.frames:
            all_frames.append(frame)

    logger.info(f"Total detected frames in job is {len(all_frames)}")

    # Detecting
    if event.is_set():

        if job.next_batch > 0:
            logger.info(f"Job resuming from batch {job.next_batch}")

        # Generate batches of frames for remaining batches
        for batchnr, (
            progress,
            batch,
            timestamp,
            video_for_frame,
            framenumbers,
        ) in video_loader.generate_batches(batch_index=job.next_batch):
            if event.is_set():
                assert isinstance(
                    batch, np.ndarray
                ), "Batch must be of type np.ndarray"
                assert isinstance(batchnr, int), "Batch number must be int"

                try:
                    logger.debug(f"Now detecting batch {batchnr}...")
                    frames = det.predict(batch, "fishy")
                    logger.debug(f"Finished detecting batch {batchnr}.")

                    # Iterate over all frames to set variables in frame
                    for n, frame in enumerate(frames):
                        abs_frame_nr = batchnr * batchsize + n

                        # Set relative frame number
                        # TODO: This breaks tracing, add another variable in frame
                        # frame.idx = framenumbers[n]

                        frame.timestamp = timestamp[n]

                        # Adds the absolute frame number to the frame before tracking.
                        # This help popuplate the timestamp for objects.
                        frame.detections = [
                            dets.set_frame(abs_frame_nr)
                            for dets in frame.detections
                        ]

                        # store detections
                        video_for_frame[framenumbers[n]].add_detection_frame(
                            frame
                        )

                        frame.idx = abs_frame_nr
                        all_frames.append(frame)

                    # Should only increment next_batch if storing of detections was successful
                    job.next_batch = batchnr + 1
                    job.progress = progress
                    repo.save()
                    logger.debug(f"Job {job.id} is {progress}% complete..")

                except KeyboardInterrupt:
                    logger.warning(
                        f"Job processing interrupted under processing of batch {batchnr}, stopping."
                    )
                    event.clear()

                if not event.is_set():
                    break
    # Tracing
    if event.is_set():
        try:
            objects = to_track(all_frames)

            for obj in objects:
                job.add_object(obj)

            repo.save()
        except KeyboardInterrupt:
            logger.warning(f"Job tracing aborted for job {job_id}.")
            event.clear()

    # Update job status
    if not event.is_set():
        logger.info(f"Pausing processing of job {job_id}.")
        job.pause()
        repo.save()
        return
    else:
        logger.info(f"Job {job_id} completed")
        job.complete()
        repo.save()


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

            process_job(next_task[0], next_task[1], event, session=session)

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

    try:
        if job.status() is Status.PENDING:
            job.queue()
            repo.save()
            logger.info(
                f"Pending job {job_id} in project {project_id} scheduled to be processed."
            )
            job_queue.put((project_id, job_id))
            return
        elif job.status() is Status.RUNNING:
            logger.info(
                f"Running job {job_id} in project {project_id} scheduled to resume."
            )
            job_queue.put((project_id, job_id))
            return
        elif job.status() is Status.PAUSED:
            logger.info(
                f"Paused job {job_id} in project {project_id} scheduled to resume."
            )
            job_queue.put((project_id, job_id))
            return
        else:
            raise JobStatusException
    except JobStatusException:
        logger.error(
            f"Cannot queue job {job_id}, it's of status {job.status()}."
        )
