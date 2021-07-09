from __future__ import annotations
import json
import os
from tracing import tracker
from typing import Dict, Set, Any
from pathlib import Path


keys_annotations = "annotations"
keys_attributes = "attributes"
keys_bbox = "bbox"
keys_category_id = "category_id"
keys_id = "id"
keys_image_id = "image_id"
keys_track_id = "track_id"


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
        annotation[keys_attributes][keys_track_id]
        for annotation in json[keys_annotations]
        if keys_track_id in annotation[keys_attributes]
    }

    for track_id in track_ids:
        detections = [
            tracker.Detection(
                tracker.BBox(*det[keys_bbox]),
                det[keys_category_id],
                1,
                det[keys_image_id],
                None,
                None,
                true_track_id=track_id,
            )
            for det in json[keys_annotations]
            if keys_track_id in det[keys_attributes]
            and det[keys_attributes][keys_track_id] is track_id
        ]
        objects[track_id] = tracker.Object(track_id)
        objects[track_id].detections = detections

    return objects


def write(objects: Dict[int, tracker.Object], file_path: Path):

    id = 0
    json_file = {keys_annotations: list()}
    for track_id, obj in objects.items():
        for d in obj.detections:
            json_file[keys_annotations].append(
                {
                    keys_id: id,
                    keys_image_id: d.frame,
                    keys_category_id: d.label,
                    keys_bbox: [
                        d.bbox.x1,
                        d.bbox.y1,
                        d.bbox.x2,
                        d.bbox.y2,
                    ],
                    keys_attributes: {
                        keys_track_id: track_id,
                    },
                }
            )


if __name__ == "__main__":
    with open(os.path.join(json_path, json_file_name)) as file:

        print(len(parse(json.load(file))))
