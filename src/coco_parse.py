from __future__ import annotations
import json
import os
from tracing import tracker
from typing import Dict, Set, Any

## Annotation object in coco json format
# {
#  "id": 12617,
#  "image_id": 11866,
#  "category_id": 6,
#  "segmentation": [],
#  "area": 44017.22379999999,
#  "bbox": [
#    1365.94,
#    0,
#    236.83,
#    185.86
#  ],
#  "iscrowd": 0,
#  "attributes": {
#    "occluded": false,
#    "track_id": 57,
#    "keyframe": false
#  }
# },

json_file_name = "instances_default.json"
json_path = "./"


def parse(json: Dict[Any, Any]) -> Dict[int, tracker.Object]:
    """Takes a dictionary and returns a dictionary indexed with tracking id and
    values `tracing.tracker.Objects`."""

    track_ids: Set[int] = set()
    objects: Dict[int, tracker.Object] = dict()

    track_ids = {
        annotation["attributes"]["track_id"]
        for annotation in json["annotations"]
        if "track_id" in annotation["attributes"]
    }

    for track_id in track_ids:
        detections = [
            tracker.Detection(
                tracker.BBox(*det["bbox"]),
                det["category_id"],
                1,
                det["image_id"],
                None,
                None,
                true_track_id=det["id"],
            )
            for det in json["annotations"]
            if "track_id" in det["attributes"]
            and det["attributes"]["track_id"] is track_id
        ]
        objects[track_id] = tracker.Object(track_id)
        objects[track_id].detections = detections

    return objects


if __name__ == "__main__":
    with open(os.path.join(json_path, json_file_name)) as file:

        print(len(parse(json.load(file))))
