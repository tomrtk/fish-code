"""Services used in this application."""
import logging

import numpy as np

from core.interface import Detector, to_track
from core.model import Job, Video

logger = logging.getLogger(__name__)

from typing import List


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

    video_loader = VideoLoader(job.videos, 50)
    det = Detector()

    all_frames = []
    for batch, timestamp in video_loader:
        assert type(batch) is np.ndarray, "Batch must be of type np.ndarray"
        frames = det.predict(batch, "fishy")

        # Iterate over all frames to set timestamps
        for n, frame in enumerate(frames):
            frame.timestamp = timestamp[n]
            all_frames.append(frame)

    objects = to_track(all_frames)

    for obj in objects:
        job.add_object(obj)

    job.complete()

    return job

    # process
    # det = core.interface.Detector()
    # det.predict(np.ndarray(()), "fishy")

    # grab 50 frames per video, regardless of file.
    # Send 50 frames to api for detection
    # Store detections
    # Trace detections and turn into objects
    # Post objects to api
    # Mark job as complete
