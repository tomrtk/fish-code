#!/usr/bin/env python3

import json
import os
from typing import Any, List

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import skimage.io as io
from pycocotools.coco import COCO
from sort import sort

from tracing import tracker


def count_SORT(tracks: List[Any]):
    """Counts idividual objects from sort"""
    count_individ_sort = set()
    for track_id in tracks:
        for track_id2 in track_id:
            count_individ_sort.add(track_id2[-1])

    return len(count_individ_sort)


def show_image(
    path: str,
    track_bbs_ids: List[Any],
    ax1: Any,
    colours: Any,
    fig: Any,
    idx: int,
):

    I = io.imread(path)  # type: ignore
    ax1.imshow(I)

    for d in track_bbs_ids[-1]:
        d = d.astype(np.int32)
        ax1.add_patch(
            patches.Rectangle(
                (d[0], d[1]),
                d[2] - d[0],
                d[3] - d[1],
                fill=False,
                lw=1,
                ec=colours[d[4] % 32, :],
                label=d[4],
            ),
        )
    plt.savefig("video/frame-{:06d}".format(idx))  # type: ignore
    fig.canvas.flush_events()
    ax1.cla()


def main():
    track_bbs_ids = []

    sort_tracker = tracker.Tracker(sort.Sort(1, 1))

    shittypath = ""

    if os.getcwd() == "/home/eirik/Git/School/bachelor/code":
        shittypath = "tracing/"

    task = "{}filtered-dataset".format(shittypath)
    json_path = "{}/annotations/instances_default.json".format(task)

    with open(json_path) as file:
        annotations_json = json.load(file)
    individ_json = set()
    for annon in annotations_json["annotations"]:
        if annon["image_id"] > 484:
            break
        try:
            individ_json.add(annon["attributes"]["track_id"])
        except:
            pass

    objects_in_json = len(individ_json)

    all_tracked_objects_in_json = len(
        [
            all_ann
            for all_ann in annotations_json["annotations"]
            if "track_id" in all_ann["attributes"]
            and all_ann["image_id"] <= 484
        ]
    )

    coco = COCO(json_path)
    catIds = coco.getCatIds(catNms=["Ørekyt"])  # type: ignore
    imgIds = coco.getImgIds(catIds=catIds)  # type: ignore

    # Create a "video". Also adds the image id so it's possible to find it for
    # display later
    frames = [(coco.loadAnns(coco.getAnnIds(imgIds=imgid)), imgid) for imgid in imgIds]  # type: ignore

    plt.ioff()  # type: ignore
    fig = plt.figure()  # type: ignore
    ax1 = fig.add_subplot(111, aspect="equal")  # type: ignore
    colours = np.random.rand(32, 3)  # used only for display

    MOTA = 0

    for idx, frame in enumerate(frames[0:484]):  # type: ignore
        img = coco.loadImgs(frame[1])[0]  # type: ignore
        path = "{}/images/{}".format(task, img["file_name"])  # type: ignore

        bbx = []
        local_detect = []

        for ann in frame[0]:  # type: ignore
            if (
                not ann["attributes"]["occluded"]
                and "track_id" in ann["attributes"]
            ):
                box = tracker.BBox.from_xywh(ann["bbox"])  # type: ignore
                detect = tracker.Detection(box, ann["category_id"], 1, idx, ann["attributes"]["track_id"])  # type: ignore
                local_detect.append(detect)
                bbx.append(detect.to_SORT())

        local_tracks = sort_tracker.update(local_detect)

        if False:
            show_image(path, track_bbs_ids, ax1, colours, fig, idx)

    miss_match = 0
    for obj in sort_tracker.get_objects().values():
        truths = set()
        for d in obj.detections:
            truths.add(d.true_track_id)
        miss_match += len(truths) - 1

    print("JSON")
    print(objects_in_json)  # type: ignore

    print("detections")
    print(len(sort_tracker.get_objects()))  # type: ignore

    MOTA = 1 - (
        (
            sort_tracker.get_misses()
            + sort_tracker.get_false_positive()
            + miss_match
        )
        / all_tracked_objects_in_json
    )

    print("MOTA:")
    print(MOTA)


if __name__ == "__main__":
    main()
