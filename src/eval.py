#!/usr/bin/env python3

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
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


def track_to_model(obj: tracker.Object) -> model.Object:
    o = model.Object(
        obj.label,  # type: ignore
        [
            model.Detection(
                model.BBox(det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2),
                det.probability,
                det.label,
                det.frame,
            )
            for det in obj.detections
        ],
    )

    frames = sorted([det.frame for det in obj.detections])

    o.time_in = datetime(1, 1, 1, 0, 0, 0) + timedelta(
        seconds=1 / 25 * frames[0]
    )
    o.time_out = datetime(1, 1, 1, 0, 0, 0) + timedelta(
        seconds=1 / 25 * frames[-1]
    )

    o._calc_label()

    return o


def detect(batch_size, images) -> List[Frame]:
    result: List[Frame] = list()

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
    return result


if __name__ == "__main__":

    from_detect: Dict[int, List[detection.schema.Detection]] = dict()
    tracked = list()
    ground_truth: Dict[int, tracker.Object] = dict()
    batch_size: int = 625
    data_folder: Path = Path.home().joinpath("Dl/dataset_coco/")
    result: List[Frame] = []
    from_file = True

    if not from_file:
        images: List[Path] = sorted(
            gen_img_paths(data_folder.joinpath("images/default"))
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
        result = detect(batch_size, images[0])

        obj_dict = {
            frame.idx: [o.to_dict() for o in frame.detections]
            for frame in result
        }

        with open("detections.json", "w") as det_file:
            det_file.write(json.dumps(obj_dict))

    with open(
        data_folder.joinpath("annotations/").joinpath(coco_parse.json_file_name)
    ) as file:
        ground_truth = coco_parse.parse(json.load(file))

    with open("detections.json", "r") as det_file:
        result = [
            Frame(k, [tracker.Detection.from_dict(det) for det in v])
            for (k, v) in json.load(det_file).items()
        ]

    print("tracking...")
    start = time.monotonic()
    track = tracker.SortTracker()
    for frame in result:
        track.update(frame.detections)
    stop = time.monotonic()
    print(f"tracking took: {stop-start}")

    print(len(ground_truth.values()))
    print(len(track.get_objects().values()))

    gt_mod_obj = [track_to_model(obj) for obj in ground_truth.values()]

    mod_obj = [track_to_model(obj) for obj in track.get_objects().values()]

    gt_mod_sorted = sorted(gt_mod_obj, key=lambda x: x.time_in)  # type: ignore
    mod_sorted = sorted(mod_obj, key=lambda x: x.time_in)  # type: ignore

    for idx in range(min(len(mod_sorted), len(gt_mod_sorted))):
        print(
            f"{mod_sorted[idx].time_in : %M:%S } | {mod_sorted[idx].time_out : %M:%S} | {len(mod_sorted[idx]._detections) : 5}  ||"
            + f"{gt_mod_sorted[idx].time_in : %M:%S} | {gt_mod_sorted[idx].time_out : %M:%S} | {len(gt_mod_sorted[idx]._detections) : 5} "
        )
