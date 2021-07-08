#!/usr/bin/env python3

from dataclasses import dataclass

from tracing import tracker
from detection import api as detection
import numpy as np
from typing import List, Optional, Dict
from core import model, services
from datetime import datetime
import torch
from PIL import Image
from io import BytesIO
from core import utils


@dataclass
class Frame:
    idx: int
    detections: List[tracker.Detection]
    timestamp: Optional[datetime] = None
    video_id: Optional[int] = None


detection.model["fishy"] = (  # type: ignore
    torch.hub.load(  # type: ignore
        "ultralytics/yolov5",
        "custom",
        path=str(detection.model_fishy_path.resolve()),
    ),
    640,
)

detection.label["fishy"] = [
    "gjedde",
    "gullbust",
    "rumpetroll",
    "stingsild",
    "ørekyt",
    "abbor",
    "brasme",
    "mort",
    "vederbuk",
]

detection.model["fishy2"] = (  # type: ignore
    torch.hub.load(  # type: ignore
        "ultralytics/yolov5",
        "custom",
        path=str(detection.model_fishy2_path.resolve()),
    ),
    768,
)

detection.label["fishy2"] = [
    "gjedde",
    "gullbust",
    "rumpetroll",
    "stingsild",
    "ørekyt",
    "abbor",
    "brasme",
    "mort",
    "vederbuk",
]

imgs: List[np.ndarray] = [np.zeros((640, 640, 3))]
track = tracker.SortTracker()

vl = services.VideoLoader(
    [
        model.Video.from_path(
            "/home/eirik/Downloads/Abbor mørkt-middels-dårlige forhold-cut-[2020-03-28_12-30-10].mp4"
        )
    ],
    batchsize=50,
)

from_detect: Dict[int, List[detection.schema.Detection]] = dict()
tracked = list()

for batchnr, (
    progress,
    batch,
    timestamp,
    video_for_frame,
    framenumbers,
) in vl.generate_batches():

    # Trying to replicate production code
    imgs = [np.array(Image.open(utils.img_to_byte(img))) for img in batch]

    from_detect = detection.detect(
        imgs,  # type: ignore
        detection.model["fishy"][0],
        detection.model["fishy"][0],
    )
    print(f"{batchnr}/{vl._total_batches}")

    result: List[Frame] = []
    for frame_no, detections in from_detect.items():
        if len(detections) == 0:
            result.append(Frame(frame_no, []))
        else:
            result.append(
                frame_no,
                [
                    tracker.Detection(
                        tracker.BBox(
                            detection.x1,
                            detection.y1,
                            detection.x2,
                            detection.y2,
                        ),
                        probability=detection.confidence,
                        label=detection.label,
                        frame=frame_no,
                        frame_id=None,
                        video_id=None,
                    )
                    for detection in detections
                ],
            )

    for frame in result:
        tracked = track.update(frame.detections)
