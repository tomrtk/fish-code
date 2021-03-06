"""Module defining API for communicating with tracing."""

from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from vendor.sort import sort

from . import tracker

tracking = FastAPI()


def make_tracker() -> tracker.SortTracker:
    """Return a SORT tracker."""
    return tracker.SortTracker(8, 1)


class BBox(BaseModel):
    """API BBox dataclass.

    See Also
    --------
    tracing.tracker.BBox
    """

    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """API detection dataclass.

    See Also
    --------
    tracing.tracker.Detection
    """

    bbox: BBox
    label: int
    probability: float
    frame: int
    frame_id: Optional[int]
    video_id: Optional[int]


class Frame(BaseModel):
    """API frame dataclass."""

    detections: List[Detection]
    idx: int


class Object(BaseModel):
    """API Object dataclass.

    See Also
    --------
    tracing.tracker.Object
    """

    track_id: int
    detections: List[Detection]
    label: int


@tracking.post("/tracking/track", response_model=List[Object])
def track_frames(
    frames: List[Frame], trk: tracker.SortTracker = Depends(make_tracker)
) -> List[Object]:
    """Create a tracker to track the recieved frames.

    Using this endpoint will not make a persistant tracker.
    """
    for idx, frame in enumerate(frames):
        detections = [
            tracker.Detection.from_api(detect.dict(), idx)
            for detect in frame.detections
        ]
        trk.update(detections)

    objects = [Object(**obj.to_dict()) for obj in trk.get_objects().values()]
    return objects
