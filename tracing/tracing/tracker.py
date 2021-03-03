from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from sort import sort


class BBox:
    """Bounding box class."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Creates a bounding box from four floats

        Parameters
        ----------
        x1 : fist X coordinate
        y1 : fist Y coordinate
        x2 : second X coordinate
        y2 : second Y coordinate
        """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @classmethod
    def from_list(cls, list: List[float]) -> BBox:
        """Creates a bounding box from a list

        Paramters
        ---------
        list : list[float]
            list on the form of [x1, y1, x2, y2]

        Returns
        -------
        BBox :
            Bounding box

        """
        return cls(*list)

    def to_list(self) -> List[float]:
        """
        Returns the boundingbox as a list

        Returns
        -------
        List[float] :
            list on the form of [x1, y1, x2, y2]
        """
        return [self.x1, self.y1, self.x2, self.y2]

    @classmethod
    def from_xywh(cls, bbox: List[float]) -> BBox:
        """
        Creates a bounding box from x, y, width, height

        Paramters
        ---------
        bbox : List[x, y, width, height]

        Returns
        -------
        BBox :
            Boundingbox
        """
        return cls(bbox[0], bbox[1], bbox[2] + bbox[0], bbox[3] + bbox[1])

    def __eq__(self, o: BBox) -> bool:
        """Checks if the two boundingboxes are witin 1 percent of eachother.

        Parameters
        ----------
        o : BBox
           Other BBox

        Returns
        bool :
            If they're equal
        """
        x1 = abs(self.x1 - o.x1)
        y1 = abs(self.y1 - o.y1)
        x2 = abs(self.x2 - o.x2)
        y2 = abs(self.y2 - o.y2)

        tol = 0.01
        return (
            x1 < tol * abs(o.x1)
            and x2 < tol * abs(o.x2)
            and y1 < tol * abs(o.y1)
            and y2 < tol * abs(o.y2)
        )

    def to_dict(self) -> Dict[str, float]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
        }


class Detection:
    """Defines a Detection as BBox, detection score, associated frame and a
    benchmark variable"""

    def __init__(
        self,
        bbox: BBox,
        label: int,
        score: float,
        frame: int,
        true_track_id: int = 0,
    ) -> None:
        """Create a detection

        Paramters
        ---------
        bbox : BBox
            The bouding box for this detection
        score : int
            Score from machine learning algorithm
        frame : int
            Frame number this detetction was found
        true_track : int
            Used for benchmarking. This is a tracking id from the dataset
        """
        self.bbox = bbox
        self.label = label
        self.score = score
        self.frame = frame
        self.true_track_id = true_track_id

    def to_SORT(self) -> np.ndarray:
        """Converts a detection to work with SORT

        Returns
        -------
        np.ndarray(1,5) :
            Detection as [x1, y1, x2, y2, score]
        """
        return np.array(np.append(self.bbox.to_list(), self.score))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bbox": self.bbox.to_dict(),
            "label": self.label,
            "score": self.score,
            "frame": self.frame,
        }

    @classmethod
    def from_dict(cls, dict: Dict[str, Any]) -> Detection:
        return cls(
            BBox(**dict["bbox"]), dict["label"], dict["score"], dict["frame"]
        )

    @classmethod
    def from_api(cls, dict: Dict[str, Any], frame):
        return cls(BBox(**dict["bbox"]), dict["label"], dict["score"], frame)


class Object:
    """Defines a object as tracking ID, detections and label"""

    def __init__(self, track_id: int) -> None:
        self.track_id = track_id
        self.detections = list()  # type: List[Detection]
        self.label = None

    def update(self, detection: Detection) -> None:
        self.detections.append(detection)
        self.label = np.bincount(self._extract_labels()).argmax()

    def _extract_labels(self) -> np.ndarray:
        return np.array([detection.label for detection in self.detections])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "detections": [detect.to_dict() for detect in self.detections],
            "label": self.label,
        }


class Tracker:
    """Abstraction over SORT. Keeps a dict of Objects"""

    def __init__(self, tracker: sort.Sort) -> None:
        """Creates a Tracker with a Sort instance and an empty dict with objects.

        Parameters
        ----------
        tracker : sort.Sort
            A Sort tracker.
        """

        self.tracker = tracker
        self.objects = {}  # type: dict[int, Object]

    def update(self, detecions: List[Detection]) -> np.ndarray:
        """Updates the Tracker.

        Paramters
        ---------
        detections : List[Detections]
            Detections to track. If there are no detections for a given frame,
            this must still be called with an empty list.


        Returns
        -------
        np.ndarray(2,5) :
            A list of tracked objects as [x1, y1, x2, y2, track_id]

        """
        if len(detecions) == 0:
            tracks = np.empty((0, 5))
        else:
            tracks = np.array([detection.to_SORT() for detection in detecions])

        self._connect_bb(
            self.tracker.update(tracks),  # type: ignore
            detecions,
        )

        return tracks

    def _connect_bb(self, tracked: np.ndarray, detect: List[Detection]) -> None:
        """Re-associates boundingboxes with a detection to determine the label
        Parameters
        ----------
        tracked : np.ndarray
            Tracked objects from self.tracker
        detect : List[Detection]
            The detections to associate the boundboxes too
        """
        for t in tracked:
            t_box = BBox(*t[0:4])
            for d in detect:
                if t_box == d.bbox:
                    self._update_object(
                        int(t[4]),
                        Detection(
                            d.bbox, d.label, d.score, d.frame, d.true_track_id
                        ),
                    )

    def _update_object(self, track_id: int, detection: Detection) -> None:
        """Updates tracked objects. If it is a new Object it will be created
        Parameters
        ----------
        track_id : int
            The tracking id of the object to update
        detection : Detection
            The detection to add to the object or create a new object from
        """
        if track_id not in self.objects:
            self.objects[track_id] = Object(track_id)

        self.objects[track_id].update(detection)

    def get_objects(self) -> dict[int, Object]:
        """Returns the object dict"""
        return self.objects

    def get_false_positive(self) -> int:
        return self.tracker.false_positives

    def get_misses(self) -> int:
        return self.tracker.miss
