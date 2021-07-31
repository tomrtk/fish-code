"""Services used in this application."""
import logging
import math
import os
import pathlib
import threading
import time
from datetime import datetime
from mimetypes import guess_type
from os.path import isdir, isfile
from queue import Empty, Queue
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy.orm import Session

import core.main
from config import get_video_root_path, load_config
from core import api
from core.interface import Detector, to_track
from core.model import Frame, Job, JobStatusException, Status, Video
from core.repository import SqlAlchemyProjectRepository as ProjectRepository

logger = logging.getLogger(__name__)
config = load_config()

job_queue: Queue = Queue()


class VideoLoader:
    """Utility class to abstract away video files and turn them into an iterator of frames."""

    def __init__(self, videos: List[Video], batchsize: int = 25) -> None:
        self.videos = videos
        self.frames = sum(v.frame_count for v in self.videos)
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
        logger.debug(f"Finding video for frame {frame}")
        if frame > sum(vid.frame_count for vid in self.videos):
            raise IndexError(f"Cannot find video index of frame {frame}.")

        for vid in self.videos:
            if curframe + vid.frame_count >= frame:
                return self.videos.index(vid), frame - curframe
            curframe += vid.frame_count
        raise IndexError(f"Cannot find video index of frame {frame}.")

    def generate_batches(
        self, batch_index: int = 0
    ) -> Generator[
        Tuple[
            int,
            Tuple[int, np.ndarray, List[datetime], Dict[int, Video], List[int]],
        ],
        None,
        None,
    ]:
        """Generate batches from list of videos, with optional batch offset.

        Parameter
        ---------
        batch_index :   int
            Batch number to start from.

        Yields
        ------
        batchnr, (progress, batch, timestamps, video_for_frame, framenumbers)    :   int, (int, list, list, dict, list)
            Yields images from video along with absolute batch number and associated values in dicts and lists.

            Batchnr is the number of batch that is returned.
            Progress is a percent representation how many batches are completed. Format is for example 72.
            Batch is a list containing np.ndarray of images in this batch.
            Timestamps is a list containing datetime for all frames in a batch.
            video_for_frame is a dict of type dict[int, Video] and stores what video a frame belongs to.
            framenumbers is a list containing ints. Where the value is the relative frame number in that video.

        Raises
        ------
        IndexError
            If batch_index parameter is larger than total batches in this VideoLoader
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
        framenumbers: List[int] = []
        video_for_frame: Dict[int, Video] = dict()
        current_batch = batch_index
        batch_start_time = time.time()
        for vid in self.videos[start_vid:]:
            if start_frame > vid.frame_count:
                raise IndexError(
                    f"Start frame of {start_frame} is too big, total frame in video is {vid.frame_count}."
                )
            for n, frame in enumerate(vid.iter_from(start_frame)):
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
) -> None:
    """Process all videos in a job and find objects.

    Parameters
    ----------
    project_id  :   int
        Project id of the porject to start processing.
    job_id      :   int
        Job id of the job to start processing.
    event       :   threading.Event
        Event that controls if the process shall keep running, or stop.
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
        if job.status() is Status.QUEUED or Status.PAUSED:
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

    def _pause_job_if_running(job: Job) -> None:
        """Pauses the job if it is running.

        Usually called when an error occurs during processing of a job.

        Parameter
        ---------
        job :   Job
            Job to pause if status is running.
        """
        if job.status() is Status.RUNNING:
            logger.info(f"Pausing processing of job {job_id}.")
            job.pause()
            repo.save()

    # make sure its sorted before we start
    job.videos.sort(key=lambda x: x.timestamp.timestamp())

    batchsize: int = config.getint("CORE", "batch_size", fallback=50)

    all_frames = []
    video_loader = VideoLoader(job.videos, batchsize=batchsize)
    try:
        det = Detector()
    except ConnectionError as e:
        logger.error(f"Could not create detector, {e}")
        _pause_job_if_running(job)
        return

    # Check if job has already processed all batches
    if job.next_batch >= video_loader._total_batches:
        logger.warning("Job has already processed all batches in video loader.")
        job.complete()
        repo.save()
        return

    # Populate all_frames variable with previously detected frames.
    for vid in job.videos:
        for frame in vid.frames:
            all_frames.append(frame)

    logger.info(f"Total detected frames in job is {len(all_frames)}")

    # Detecting
    if event.is_set():

        if job.next_batch > 0:
            logger.info(f"Job resuming from batch {job.next_batch}")

        try:
            # Generate batches of frames for remaining batches
            for batchnr, (
                progress,
                batch,
                timestamp,
                video_for_frame,
                framenumbers,
            ) in video_loader.generate_batches(batch_index=job.next_batch):
                if not event.is_set():
                    break

                assert isinstance(
                    batch, np.ndarray
                ), "Batch must be of type np.ndarray"
                assert isinstance(batchnr, int), "Batch number must be int"

                try:
                    logger.debug(f"Now detecting batch {batchnr}...")
                    frames = det.predict(batch, "fishy")
                    logger.debug(f"Finished detecting batch {batchnr}.")
                except ConnectionError as e:
                    logger.error(e)
                    _pause_job_if_running(job)
                    return
                except RuntimeError as e:
                    logger.error(e)
                    _pause_job_if_running(job)
                    return

                # Iterate over all frames to set variables in frame
                for n, frame in enumerate(frames):
                    abs_frame_nr = batchnr * batchsize + n

                    frames[n].idx = framenumbers[n]

                    frames[n].timestamp = timestamp[n]

                    # Adds the absolute frame number to the frame before tracking.
                    # This help popuplate the timestamp for objects.
                    frames[n].detections = [
                        dets.set_frame(
                            abs_frame_nr,
                            framenumbers[n],
                            video_for_frame[framenumbers[n]].id,
                        )
                        for dets in frames[n].detections
                    ]

                    # store detections
                    video_for_frame[framenumbers[n]].add_detection_frame(
                        frames[n]
                    )

                    # frame.idx = abs_frame_nr
                    all_frames.append(frames[n])
                    all_frames.append(frame)

                # Should only increment next_batch if storing of detections was successful
                job.next_batch = batchnr + 1
                job.progress = progress
                repo.save()
                logger.debug(f"Job {job.id} is {progress}% complete..")

        except KeyboardInterrupt:
            logger.warning(
                "Job processing interrupted under processing, stopping."
            )
            _pause_job_if_running(job)
            event.clear()

    # Tracing
    if event.is_set():
        try:
            objects = to_track(all_frames)

            for obj in objects:
                job.add_object(obj)

            repo.save()
        except KeyboardInterrupt:
            logger.warning(f"Job tracing aborted for job {job_id}.")
            _pause_job_if_running(job)
            event.clear()

        logger.info(f"Job {job_id} completed")
        job.complete()
        repo.save()


class SchedulerThread(threading.Thread):
    """Wrapper class around Thread to handle exceptions in thread."""

    def run(self) -> None:
        """Wrap method around target function to catch exception.

        Called when `.start` is called on `Thread`.
        """
        self.exc = None
        self.ret = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)  # type: ignore
        except BaseException as e:
            self.exc = e

    def join(self) -> Any:  # type: ignore
        """Wrap method around `Thread` join to propagate exception."""
        super().join()
        if self.exc:
            raise RuntimeError("Exception in thread") from self.exc
        return self.ret


def schedule(event: threading.Event) -> None:
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

            if core.main.sessionfactory is None:
                raise RuntimeError("Sessionfactory is not made")

            session = core.main.sessionfactory()

            process_job(next_task[0], next_task[1], event, session=session)

        job_queue.task_done()
    logger.info("Scheduler ending.")


# Threes signalling event to stop.
schedule_event = threading.Event()
schedule_event.set()
# Defining scheduler thread
schedule_thread = SchedulerThread(
    target=schedule, args=(schedule_event,), daemon=True
)


def stop_scheduler() -> None:
    """Stop the scheduler thread."""
    logger.info("Stopping")

    # Clear queue, TODO Store jobs in queue and handle running jobs.
    # job_queue.queue.clear()

    # signal scheduler_thread to close.
    schedule_event.clear()

    # wait for thread to close. At most 1s if not processing a job.
    schedule_thread.join()
    logger.info("Stopped")


def start_scheduler() -> None:
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


def queue_job(project_id: int, job_id: int, session: Session) -> None:
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


def get_job_objects(
    project_id: int, job_id: int, start: int, length: int
) -> Optional[Dict[str, Any]]:
    """Collect a set of `Objects` from job.

    Collect a set of `Objects` from `start` to `start + length` part of job
    if found.

    Parameters
    ----------
    project_id : int
        id of project the job is part of.
    job_id : int
        id of job the objects are part of.
    start : int
        first instance of object returned(0 based index).
    length : int
        totalt number of objects to re returned as part of this request.

    Raises
    ------
    RuntimeError
        If no database session can be established.

    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary with key `data` with Objects and `total_objects` with
        total number of objects in job.
    """
    if core.main.sessionfactory is None:
        raise RuntimeError("Could not create a database session")

    repo = ProjectRepository(core.main.sessionfactory())

    project = repo.get(project_id)

    if project is None:
        return None

    job = project.get_job(job_id)

    if job is None:
        return None

    response: Dict[str, Any] = {}
    response["total_objects"] = len(job._objects)
    response["data"] = job._objects[start : start + length]

    return response


def get_directory_listing(
    path: Optional[str] = None,
) -> List[Optional[Union[Dict[str, Any], str]]]:
    """Get contents found in a given directory. Does not search recursivly.

    Parameters
    ----------
    path    :   str
        Path to the folder one wants to get listing from.

    Raises
    ------
    NotADirectoryError
        When the given path is a file and not a directory.

    FileNotFoundError
        Directory cannot be found at a given path.

    Returns
    -------
    Dict
        jsTree formatted json containing information about root node at path.
    """
    if path is None:
        directory = config.get(
            "CORE", "video_root_path", fallback=str(get_video_root_path())
        )
    else:
        directory = path

    normalized_path = pathlib.Path(directory)

    tree: List[Optional[Union[Dict[str, Any], str]]] = list()
    root_node: Dict[str, Any] = dict()
    child_list = []

    if isfile(normalized_path):
        raise NotADirectoryError("Path must be a directory.")

    if not isdir(normalized_path):
        raise FileNotFoundError(
            f"Directory at '{normalized_path}' was not found."
        )

    if not os.access(normalized_path, os.R_OK):
        raise PermissionError(
            f"Directory at '{normalized_path}' is inaccessable."
        )

    for p in normalized_path.iterdir():
        if p.is_dir():
            child_list.append(
                {
                    "id": str(p.as_posix()),
                    "text": p.name,
                    "type": "folder",
                    "children": True,
                }
            )
        else:
            child_list.append(
                {
                    "id": str(p.as_posix()),
                    "text": p.name,
                    "type": str(guess_type(p)[0])
                    if guess_type(p)[0]
                    else "file",
                }
            )

    # Create root node
    root_name = normalized_path.name
    root_node = {
        "id": str(normalized_path.as_posix()),
        "text": "/" if root_name == "" else root_name,
        "type": "folder",
        "children": sorted(child_list, key=lambda u: u["id"]),
    }

    tree.append(root_node)

    return tree
