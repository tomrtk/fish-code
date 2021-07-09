#!/usr/bin/env python3

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from multiprocessing.pool import Pool as multiproc_pool
from pathlib import Path
from typing import Dict, List, Optional

import cv2 as cv
import numpy as np
import torch

import coco_parse
from core import model
from detection import api as detection
from tracing import tracker


@dataclass
class Frame:
    idx: int
    detections: List[tracker.Detection]
    timestamp: Optional[datetime] = None
    video_id: Optional[int] = None


def scale_convert(img: np.ndarray) -> np.ndarray:
    new_img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # type: ignore

    new_img = cv.resize(  # type: ignore
        new_img,
        (model.VIDEO_DEFAULT_WIDTH, model.VIDEO_DEFAULT_HEIGHT),
        interpolation=cv.INTER_AREA,  # type: ignore
    )
    return new_img


def read_img(img_path: Path) -> np.ndarray:
    return scale_convert(cv.imread(img_path.as_posix(), cv.IMREAD_UNCHANGED))  # type: ignore


def gen_batch(size: int, images: List[Path]) -> List[np.ndarray]:
    for batch_nr in range(len(images) // size):
        start_time = time.monotonic()
        start = 0
        batch: List[np.ndarray] = list()
        with multiproc_pool(os.cpu_count()) as pool:
            batch = pool.map(
                read_img,
                images[start : start + size],
                size // os.cpu_count(),  # type: ignore
            )
        yield batch_nr, len(images) // size, batch  # type: ignore
        start = start + size
        print(f"time spent: {round(time.monotonic()-start_time, 2)}")


def gen_img_paths(path: Path) -> List[Path]:
    return [path.joinpath(file) for file in os.listdir(path)]


def det_to_track(det: detection.schema.Detection, frame_no):
    return tracker.Detection(
        tracker.BBox(
            det.x1,
            det.y1,
            det.x2,
            det.y2,
        ),
        probability=det.confidence,
        label=det.label,
        frame=frame_no,
        frame_id=None,
        video_id=None,
    )


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

batch: List[np.ndarray] = [np.zeros((640, 640, 3))]
from_detect: Dict[int, List[detection.schema.Detection]] = dict()
tracked = list()
ground_truth: Dict[int, tracker.Object] = dict()
batch_size: int = 625
result: List[Frame] = []

track = tracker.SortTracker()
images: List[Path] = sorted(
    gen_img_paths(Path.home().joinpath("Dl/dataset_coco/images/default"))
)

with open(
    os.path.join(coco_parse.json_path, coco_parse.json_file_name)
) as file:
    ground_truth = coco_parse.parse(json.load(file))

for batchnr, total_batch, batch in gen_batch(batch_size, images):
    print(f"{batchnr}/{total_batch}")

    from_detect = detection.detect(
        batch,
        detection.model["fishy"][0],
        detection.model["fishy"][1],
    )

    for frame_no, detections in from_detect.items():
        frame_no = frame_no + (batch_size * batchnr)
        if len(detections) == 0:
            result.append(Frame(frame_no, []))
        else:
            result.append(
                Frame(
                    frame_no,
                    [det_to_track(det, frame_no) for det in detections],
                )
            )

for frame in result:
    track.update(frame.detections)

print(len(ground_truth.values()))
print(len(track.get_objects().values()))
