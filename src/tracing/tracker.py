"""Module defines BBox, Detection, Object and Tracker."""
from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

import numpy as np

from vendor.sort import sort


class BBox:
    """Bounding box class."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Create a bounding box from four floats.

        Parameters
        ----------
        x1 : fist X coordinate
        y1 : fist Y coordinate
        x2 : second X coordinate
        y2 : second Y coordinate
        """
        self.x1: float = x1
        self.y1: float = y1
        self.x2: float = x2
        self.y2: float = y2

    @classmethod
    def from_list(cls, list: list[float]) -> BBox:
        """Create a bounding box from a list.

        Paramters
        ---------
        list : list[float]
            list on the form of [x1, y1, x2, y2]

        Returns
        -------
        BBox :
            Bounding box

        """
        if len(list) != 4:
            raise ValueError(f"Length of bbox is {len(list)}, expected 4")

        return cls(*list)

    def to_list(self) -> list[float]:
        """Return the boundingbox as a list.

        Returns
        -------
        List[float] :
            list on the form of [x1, y1, x2, y2]
        """
        return [self.x1, self.y1, self.x2, self.y2]

    @classmethod
    def from_xywh(cls, bbox: list[float]) -> BBox:
        """Create a bounding box from x, y, width, height.

        Paramters
        ---------
        bbox : List[x, y, width, height]

        Returns
        -------
        BBox :
            Boundingbox
        """
        if len(bbox) != 4:
            raise ValueError(f"Length of bbox is {len(bbox)}, expected 4")

        return cls(bbox[0], bbox[1], bbox[2] + bbox[0], bbox[3] + bbox[1])

    def __eq__(self, o: object) -> bool:
        """Check if the two boundingboxes are witin 1 percent of eachother.

        Parameters
        ----------
        o : BBox
           Other BBox

        Return
        ------
        bool :
            If they're equal
        """
        if not isinstance(o, BBox):
            raise NotImplementedError

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

    def to_dict(self) -> dict[str, float]:
        """Convert boundingbox to dict.

        Return
        ------
        Dict[str, float] :
            {"x1": float, "y1": float, "x2": float, "y2": float}
        """
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
        }


class Detection:
    """Defines a Detection as BBox, detection score, associated frame and a benchmark variable."""

    def __init__(
        self,
        bbox: BBox,
        label: int,
        probability: float,
        frame: int,
        frame_id: int | None,
        video_id: int | None,
        true_track_id: int = 0,
    ) -> None:
        """Create a detection.

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
        self.bbox: BBox = bbox
        self.label: int = label
        self.probability: float = probability
        self.frame: int = frame
        self.frame_id: int | None = frame_id
        self.video_id: int | None = video_id
        self.true_track_id: int = true_track_id

    def to_dict(self) -> dict[str, Any]:
        """Convert self to dict.

        Return
        ------
        Dict[str, Any] :
            {"bbox" : Dict[str, float], "label": int, "score": float, "frame": int }
        """
        return {
            "bbox": self.bbox.to_dict(),
            "label": self.label,
            "probability": self.probability,
            "frame_id": self.frame_id,
            "video_id": self.video_id,
            "frame": self.frame,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Detection:
        """Create a detection from a dictionary.

        See Also
        --------
        cls.to_dict()
        """
        return cls(
            bbox=BBox(**data["bbox"]),
            label=data["label"],
            probability=data["probability"],
            frame_id=data["frame_id"],
            video_id=data["video_id"],
            frame=data["frame"],
        )

    @classmethod
    def from_api(cls, data: dict[str, Any], frame: int) -> Detection:
        """Specialized from_dict used when converting from API.

        Paramter
        --------
        dict : Dict[str, Any]
            { "bbox" : Dict[str, float], "label": int, "score": float }
        frame : int
            The frame number where this detection was found

        See Also
        --------
        cls.from_dict()
        cls.to_dict()
        tracing.api.Detection
        """
        return cls(
            bbox=BBox(**data["bbox"]),
            label=data["label"],
            probability=data["probability"],
            frame_id=data["frame_id"],
            video_id=data["video_id"],
            frame=frame,
        )


class Object:
    """Defines a object as tracking ID, detections and label."""

    def __init__(self, track_id: int) -> None:
        """Create a minimal Object.

        Parameter
        ---------
        track_id : int
            Tracking id given from the tracker

        See Also
        --------
        tracing.tracker.Tracker
        """
        self.track_id: int = track_id
        self.detections: list[Detection] = list()
        self.label: int | None = None

    def update(self, detection: Detection) -> None:
        """Update the detections for this Object.

        Also updates it's label based on the labels found in it's detections.


        Parameter
        ---------
        detection : Detection
            A new detection to add to the detection list.
        """
        if detection.frame in [detect.frame for detect in self.detections]:
            raise ValueError(
                f"A detection with frame number {detection.frame} already exist"
            )

        self.detections.append(detection)
        self.label = np.bincount(self._extract_labels()).argmax()

    def _extract_labels(self) -> np.ndarray:
        """Return a list of labels from associated detections."""
        return np.array([detection.label for detection in self.detections])

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict.

        See Also
        --------
        tracing.tracker.Detection.to_dict()
        """
        return {
            "track_id": self.track_id,
            "detections": [detect.to_dict() for detect in self.detections],
            "label": self.label,
        }


class AbstractTracker(abc.ABC):
    """Abstract tracker class."""

    def __init__(self) -> None:
        self._objects: dict[int, Object] = dict()

    def update(self, detections: list[Detection]) -> None:
        """Update the tracker."""
        raise NotImplementedError

    def get_objects(self) -> dict[int, Object]:
        """Return the object dict."""
        return self._objects

    def get_false_positive(self) -> int:
        """Get the false positives from the tracker. Used for benchmarking."""
        raise NotImplementedError

    def get_misses(self) -> int:
        """Get the misses from the tracker. Used for benchmarking."""
        raise NotImplementedError


class SortTracker(AbstractTracker):
    """Abstraction over SORT.

    Methods
    -------
    update()
        Updates the internal object list with new detections. Can be used in an
        online fashion.
    get_objects()
        Direct implementation from AbstractTracker. Returns dictionary with
        objects.
    get_false_positives()
        Returns false positives from Sort.
    get_misses()
        Returns misses from Sort.
    """

    def __init__(
        self,
        max_age: int = 1,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
    ) -> None:
        """Create a Tracker with a Sort instance and an empty dict with objects.

        Parameter
        ---------
        tracker : sort.Sort
            A Sort tracker.
        """
        super().__init__()
        self._tracker: sort.Sort = sort.Sort(max_age, min_hits, iou_threshold)

    def update(self, detecions: list[Detection]) -> None:
        """Update the Tracker.

        Paramter
        --------
        detections : List[Detections]
            Detections to track. If there are no detections for a given frame,
            this must still be called with an empty list.


        Return
        ------
        np.ndarray(2,5) :
            A list of tracked objects as [x1, y1, x2, y2, track_id]
        """
        if len(detecions) == 0:
            tracks = np.empty((0, 5))
        else:
            tracks = np.array(
                [self._convert(detection) for detection in detecions]
            )

        self._connect_bb(
            self._tracker.update(tracks),
            detecions,
        )

    @staticmethod
    def _convert(detection: Detection) -> np.ndarray:
        """Convert a detection to work with SORT.

        Return
        ------
        np.ndarray(1,5) :
            Detection as [x1, y1, x2, y2, score]
        """
        return np.array(
            np.append(detection.bbox.to_list(), detection.probability)
        )

    def _connect_bb(self, tracked: np.ndarray, detect: list[Detection]) -> None:
        """Re-associate boundingboxes with a detection to determine the label.

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
                            bbox=d.bbox,
                            label=d.label,
                            probability=d.probability,
                            frame=d.frame,
                            frame_id=d.frame_id,
                            video_id=d.video_id,
                            true_track_id=d.true_track_id,
                        ),
                    )
                    break

    def _update_object(self, track_id: int, detection: Detection) -> None:
        """Update tracked objects.

        If it is a new Object it will be created

        Parameter
        ---------
        track_id : int
            The tracking id of the object to update
        detection : Detection
            The detection to add to the object or create a new object from
        """
        if track_id not in self._objects:
            self._objects[track_id] = Object(track_id)

        self._objects[track_id].update(detection)

    def get_false_positive(self) -> int:
        """Get the false positives from the tracker. Used for benchmarking."""
        return self._tracker.false_positives

    def get_misses(self) -> int:
        """Get the misses from the tracker. Used for benchmarking."""
        return self._tracker.miss
