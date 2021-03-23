"""Module defining API for communicating with tracing."""

from typing import List

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sort import sort

from . import tracker

tracking = FastAPI()


def make_tracker():
    """Return a SORT tracker."""
    return tracker.Tracker(sort.Sort())


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
    frames: List[Frame], trk: tracker.Tracker = Depends(make_tracker)
):
    """Create a tracker to track the recieved frames.

    Using this endpoint will not make a persistant tracker.
    """
    for idx, frame in enumerate(frames):
        detections = [
            tracker.Detection.from_api(detect.dict(), frame.idx)
            for detect in frame.detections
        ]
        trk.update(detections)

    objects = [Object(**obj.to_dict()) for obj in trk.get_objects().values()]
    return objects
