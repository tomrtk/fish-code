"""Services used in this application."""
import logging

import numpy as np

import core.interface
from core.model import Frame, Job, Video

logger = logging.getLogger(__name__)


def process_job(job: Job):
    """Process all videos in a job and finds objects."""
    chunk_frames = 50

    # make sure its sorted before we start
    job.videos.sort(key=lambda x: x.timestamp.timestamp())

    frame_index = 0

    total_frames = job.total_frames()
    detections = list()

    while frame_index < total_frames:

        if (frame_index + chunk_frames) > total_frames:
            chunk_frames = total_frames - frame_index

        logger.debug(
            f"Grabbing {chunk_frames} frames from videos, total of {total_frames} frames."
        )

        # process
        # det = core.interface.Detector()
        # det.predict(np.ndarray(()), "fishy")

        frame_index += chunk_frames

        # grab 50 frames per video, regardless of file.
        # Send 50 frames to api for detection
        # Store detections
        # Trace detections and turn into objects
        # Post objects to api
        # Mark job as complete
