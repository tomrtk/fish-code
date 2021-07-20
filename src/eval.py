#!/usr/bin/env python3

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from multiprocessing.pool import Pool as multiproc_pool
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from matplotlib import pyplot as plt


import cv2 as cv
import numpy as np
import random
import torch
import itertools

from traitlets.traitlets import Integer

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


def outline(
    img: np.ndarray,
    bbx: model.BBox,
    color: Tuple[int, int, int],
    thickness: int,
) -> np.ndarray:
    """Convert numpy array to image and outline detection.

    Parameters
    ----------
    img     : np.ndarray
            Imagedata as numpy.ndarray
    bbx    : model.BBox
            Boundingbox associated with the detection

    Returns
    -------
    np.ndarray
            image encoded as jpeg
    """
    new_img = cv.rectangle(  # type: ignore
        img,
        (int(bbx.x1), int(bbx.y1)),
        (int(bbx.x2), int(bbx.y2)),
        color,
        thickness,
    )

    return new_img


def outline_objects(
    images: List[np.ndarray], objects: list[model.Object], thickness=1
) -> List[np.ndarray]:
    colors = [
        (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )
        for _ in range(len(objects))
    ]

    for obj in objects:
        for det in obj._detections:
            imgs[det.frame] = outline(
                images[det.frame],
                det.bbox,
                colors[obj.id],  # type: ignore
                thickness=thickness,
            )

    return imgs  # type: ignore


def make_video(imgs: List[np.ndarray]):

    out = cv.VideoWriter(  # type: ignore
        "output_obj.avi",
        cv.VideoWriter_fourcc(*"DIVX"),  # type: ignore
        25,
        (model.VIDEO_DEFAULT_WIDTH, model.VIDEO_DEFAULT_HEIGHT),
    )

    [out.write(cv.cvtColor(img, cv.COLOR_RGB2BGR)) for img in imgs]  # type: ignore
    out.release()


def scale_convert(img: np.ndarray) -> Optional[np.ndarray]:
    if img is None:
        return img
    new_img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # type: ignore

    return new_img


def read_img(img_path: Path) -> Optional[np.ndarray]:
    img = cv.cvtColor(cv.imread(img_path.as_posix(), cv.IMREAD_COLOR), cv.COLOR_BGR2RGB)  # type: ignore
    return img


def gen_batch(size: int, images: List[Path]) -> List[np.ndarray]:
    start = 0
    for batch_nr in range(len(images) // size):
        start_time = time.monotonic()
        batch: List[np.ndarray] = list()
        end = start + size
        print(f"{start} : {end}")
        if end > len(images):
            end = len(images)
        with multiproc_pool(os.cpu_count()) as pool:
            batch = pool.map(
                read_img,
                images[start:end],
                size // os.cpu_count(),  # type: ignore
            )

        batch = [
            cv.resize(  # type: ignore
                img,
                (model.VIDEO_DEFAULT_WIDTH, model.VIDEO_DEFAULT_HEIGHT),
                interpolation=cv.INTER_AREA,  # type: ignore
            )
            for img in batch
            if img is not None
        ]
        yield batch_nr, len(images) // size, batch  # type: ignore
        start = end
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
                bbox=model.BBox(
                    det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2
                ),
                probability=det.probability,
                label=det.label,
                frame=det.frame,
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

    result: List[Frame] = list()
    from_detect: Dict[int, List[detection.schema.Detection]] = dict()

    for batchnr, total_batch, batch in gen_batch(batch_size, images):
        print(f"{batchnr}/{total_batch}")

        from_detect = detection.detect(
            batch,
            detection.model["fishy"][0],
            detection.model["fishy"][1],
        )

        for frame_no, detections in from_detect.items():
            frame_no_new = frame_no + (batch_size * batchnr)
            if len(detections) == 0:
                result.append(Frame(frame_no_new, []))
            else:
                result.append(
                    Frame(
                        frame_no_new,
                        [det_to_track(det, frame_no_new) for det in detections],
                    )
                )

    return result


if __name__ == "__main__":

    tracked = list()
    ground_truth: Dict[int, tracker.Object] = dict()
    batch_size: int = 600
    data_folder: Path = Path(
        "/mnt/storage/trening/datasett_mort_stim_gode_coco/"
    )
    images_path = data_folder.joinpath("images")

    images: List[Path] = sorted(gen_img_paths(images_path))
    result: List[Frame] = []
    from_file = True

    if not from_file:

        result = detect(batch_size, images)

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

    args: List[Tuple[int, int]] = itertools.permutations(  # type: ignore
        np.arange(1, 25), r=2
    )

    track_res = list()
    args_list = list()
    gt_mod_obj = [track_to_model(obj) for obj in ground_truth.values()]
    gt_mod_sorted = sorted(gt_mod_obj, key=lambda x: x.time_in)  # type: ignore
    best: Optional[Tuple[int, Tuple[int, int]]] = None

    for attempt, arg in enumerate(args):

        start = time.monotonic()
        track = tracker.SortTracker(*arg)
        for frame in result:
            track.update(frame.detections)
        stop = time.monotonic()

        mod_obj = [track_to_model(obj) for obj in track.get_objects().values()]

        err: int = (len(gt_mod_obj) - len(mod_obj)) ** 2
        track_res.append(err)
        if best is None:
            best = (err, arg)
        elif best[0] > len(gt_mod_obj):
            best = (err, arg)

    print(best)
    plt.plot(track_res)
    plt.show()

    exit()
