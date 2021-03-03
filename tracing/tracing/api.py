from typing import List

import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sort import sort

from . import tracker

tracking = FastAPI()


def make_tracker():
    return tracker.Tracker(sort.Sort())


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    bbox: BBox
    label: int
    score: float
    frame: int


class Frame(BaseModel):
    detections: List[Detection]
    idx: int


class Object(BaseModel):
    track_id: int
    detections: List[Detection]
    label: int


@tracking.post("/tracking/track", response_model=List[Object])
def track_frames(
    frames: List[Frame], trk: tracker.Tracker = Depends(make_tracker)
):
    for idx, frame in enumerate(frames):
        detections = [
            tracker.Detection.from_api(detect.dict(), idx)
            for detect in frame.detections
        ]
        trk.update(detections)

    objects = [Object(**obj.to_dict()) for obj in trk.get_objects().values()]
    return objects


if __name__ == "__main__":
    uvicorn.run(tracking, host="0.0.0.0", port=8000)
