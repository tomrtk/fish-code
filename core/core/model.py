"""Module defining the domain model entities."""
from __future__ import annotations

import logging
import math
import os.path
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import cv2 as cv
import numpy as np

import core

logger = logging.getLogger(__name__)

VIDEO_DEFAULT_HEIGHT: int = 360
VIDEO_DEFAULT_WIDTH: int = 640


class TimestampNotFoundError(Exception):
    """Exception to raise if no timestamp are found."""

    pass


class Status(str, Enum):
    """Enum for job progress."""

    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    DONE = "Done"
    QUEUED = "Queued"


class Video:
    """Video class.

    This class provides various functions to retrieve data from a video file.

    Parameters
    ----------
    path            :   str
                        Path to this video file as a string
    frames          :   int
                        Number of frames in the video
    fps             :   int
                        Frames per second in the video
    width           :   int
                        Width in pixels
    height          :   int
                        Height in pixels
    timestamp       :   datetime
                        timestamp for when the video starts
    output_width    :   int
                        Frame output width. Default to `VIDEO_DEFAULT_WIDTH`
                        constant.
    output_height   :   int
                        Frame output height. Default to
                        `VIDEO_DEFAULT_HEIGHT` constant.

    Attribute
    ---------
    _path   :   str
            Path to the video file associated with the video.
    id      :   Optional[int]
            Video id from repository(database).

    Methods
    -------
    exists()
        Checks if the path is valid, by checking if its a file on the disk.
    from_path(path: str)
        Named constructor that creates and populates a video object with
        metadata read from the file. Raises FileNotFoundError if the
        file could not be read, or is not a video file.
    timestamp_at(idx: int)
        Return timestamp at index in video as a `datetime` object.

    Examples
    --------
    >>> video = Video.from_path("test.mp4")
    >>> one_frame = video[5]
    >>> print(one_frame.shape)
    (720, 1280, 3)
    >>> many_frames = video[5,10]
    >>> print(many_frames.shape)
    (5, 720, 1280, 3)
    >>> len(video)
    20
    >>> many_frames = video[10:]
    >>> print(many_frames.shape)
    (10, 720, 1280, 3)

    Raises
    ------
    FileNotFoundError
        If error reading video file when creating `from_path()`.
    TimestampNotFound
        If no timestamp where found when creating `from_path()`.
    """

    def __init__(
        self,
        path: str,
        frames: int,
        fps: int,
        width: int,
        height: int,
        timestamp: datetime,
        output_width: int = VIDEO_DEFAULT_WIDTH,
        output_height: int = VIDEO_DEFAULT_HEIGHT,
    ) -> None:
        self.id: Optional[int] = None
        self._path: str = path
        self.frames: int = frames
        self.fps: int = fps
        self.width: int = width
        self.height: int = height
        self.output_width: int = output_width
        self.output_height: int = output_height
        self.timestamp: datetime = timestamp
        self._current_frame = 0
        self._video_capture: cv.VideoCapture = cv.VideoCapture(self._path)  # type: ignore

        if output_height <= 0 or output_width <= 0:
            raise ValueError(
                "Output width and height must be positive, not %s, %s",
                output_width,
                output_height,
            )

    def _scale_convert(self, img: np.ndarray) -> np.ndarray:
        """Convert and scale image using OpenCV.

        Converts image from BGR to RGB, and scales down to `self.output_{height,width}`

        Parameter
        ---------
        img : np.ndarray
            image to convert and scale

        Return
        ------
        ndarray:
            Scaled and converted image
        """
        new_img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # type: ignore

        new_img = cv.resize(  # type: ignore
            new_img,
            (self.output_width, self.output_height),
            interpolation=cv.INTER_AREA,  # type: ignore
        )
        return new_img

    def vidcap_release(self):
        """Release Video Capture."""
        self._video_capture.release()

    def __iter__(self):
        """Class iterator.

        This never releases the VideoCapture. Not sure if it's kept alive, and
        if that's the case, this could cause a memory leak. To make sure this
        gets released, run `self.vidcap_release()`.

        See Also
        --------
        Video.vidcap_release()

        """
        self._video_capture = cv.VideoCapture(self._path)  # type: ignore
        self._video_capture.set(cv.CAP_PROP_POS_MSEC, 0)  # type: ignore
        return self

    def __next__(self) -> np.ndarray:
        """Get next item from iterator.

        Return
        ------
        np.ndarray
            One frame of video as `ndarray`.

        """
        err, img = self._video_capture.read()
        if not err:
            self.vidcap_release()
            raise StopIteration
        return self._scale_convert(img)

    def __get__(self, key) -> np.ndarray:
        """Get one frame of video.

        Used by `__getitem__` when only one key is given.

        Returns
        -------
        numpy.ndarray
            One frame of video as `ndarray`.

        Raise
        -----
        RuntimeError :
            if OpenCV fails to either read or set properties.
        """
        if key < 0:
            raise IndexError

        if key >= self.frames:
            raise IndexError

        self._video_capture = cv.VideoCapture(self._path)  # type: ignore
        retval = self._video_capture.set(cv.CAP_PROP_POS_FRAMES, key)  # type: ignore

        if not retval:
            raise RuntimeError(  # pragma: no cover
                f"Unexpected error when setting catpure property, {retval}"
            )

        retval, img = self._video_capture.read()

        if not retval:
            raise RuntimeError(
                f"Unexpected error when reading frame at {key}"
            )  # pragma: no cover

        self._video_capture.release()

        return self._scale_convert(img)

    def __getitem__(self, interval: Union[slice, int]):
        """Get a slice of video.

        Get a interval of frames from video, `variable[start:stop:step].
        Note `step` is not implemented and will raise a `exception`.

        Examples
        --------
        >>> video = Video.from_path("test.mp4")
        >>> one_frame = video[5]
        >>> print(one_frame.shape)
        (720, 1280, 3)
        >>> many_frames = video[5,10]
        >>> print(many_frames.shape)
        (5, 720, 1280, 3)

        Returns
        -------
        numpy.ndarray
            Interval of frames returned in format `(frame, height, width, channels)`

        See Also
        --------
        __get__     :   Used when only start in slice given.

        Raise
        -----
        RuntimeError :
            if OpenCV fails to either read or set properties.
        """
        # If only one key is given
        if isinstance(interval, int):
            return self.__get__(interval)

        if not isinstance(interval, slice):
            raise TypeError("%s is not %s", type(interval), type(slice))

        if isinstance(interval.stop, int) and interval.stop >= self.frames:
            raise IndexError(
                "Index for stop in slice more then frame count %s", self.frames
            )

        if interval.start < 0:
            raise IndexError("Index for start in slice is less then 0")

        # Slice stepping is not implemented.
        if interval.step != None:
            raise NotImplementedError("Step in slicing is not implemented")

        # If slicing with `video[0:] or video[0:-1]` all frames from start to
        # end or end-1 of video is wanted.
        if interval.stop == None:
            stop = self.frames
        elif interval.stop < 0:
            stop = self.frames + interval.stop
            print(stop)
        else:
            stop = interval.stop

        numbers = stop - interval.start

        self._video_capture = cv.VideoCapture(self._path)  # type: ignore
        retval = self._video_capture.set(cv.CAP_PROP_POS_FRAMES, interval.start)  # type: ignore

        if not retval:
            raise RuntimeError("Unexpected error")  # pragma: no cover

        frames = []

        for _ in range(numbers):
            retval, img = self._video_capture.read()

            if not retval:
                raise RuntimeError("Unexpected error")  # pragma: no cover
            frames.append(self._scale_convert(img))

        self._video_capture.release()
        return np.array(frames)

    def __len__(self) -> int:
        """Get length of video in frames."""
        return self.frames

    def exists(self) -> bool:
        """Check if the file path is a valid file."""
        return os.path.isfile(self._path)

    @classmethod
    def from_path(
        cls,
        path: str,
        output_width: int = VIDEO_DEFAULT_WIDTH,
        output_height: int = VIDEO_DEFAULT_HEIGHT,
    ) -> Video:
        """Named constructor to create a `Video` from path.

        Examples
        --------
        >>> video = Video.from_path("video.mp4")
        >>> type(video)
        <class 'core.model.Video'>

        Raises
        ------
        FileNotFoundError
            If `path` to file do not exists.
        """
        if not Path(path).exists():
            raise FileNotFoundError("Video file %s not found.", path)

        timestamp = parse_str_to_date(Path(path).name)
        if timestamp == None:
            raise TimestampNotFoundError(f"No timestamp found for file {path}")

        height, width, fps, frame_numbers = _get_video_metadata(path)

        return cls(
            path=path,
            frames=frame_numbers,
            fps=fps,
            width=width,
            height=height,
            timestamp=timestamp,
            output_width=output_width,
            output_height=output_height,
        )

    def timestamp_at(self, idx: int) -> datetime:
        """Return timestamp at index in video.

        Parameter
        ---------
        idx : int
            Index in video.

        Return
        ------
        datetime :
            Timestamp for the frame at index.

        """
        if idx > self.frames:
            raise IndexError
        if idx < 0:
            raise IndexError

        return self.timestamp + (timedelta(seconds=int(idx / self.fps)))


def parse_str_to_date(string: str, offset_min: int = 30) -> Optional[datetime]:
    """Parse string to date.

    Input can either be a string with a date, or a string with a date and
    offset. If an offset is found, `offset_min` will be multiplied with the
    offset and the result will be to the returned date.

    Parameter
    ---------
    string: str
        string to parse to date on the format:
        `[yyyy-mm-dd_hh-mm-ss]` or `[yyyy-mm-dd_hh-mm-ss]-xxx`
    offset_min: int
        Minutes to offset for each increment


    Return
    ------
    datetime :
        parsed datetime object, or None if unsuccessful

    Example
    -------
    >>> parse_str_to_date("test-[2020-03-28_12-30-10]-000.mp4")
    datetime.datetime(2020, 3, 28, 12, 30, 10)
    >>> parse_str_to_date("test-[2020-03-28_12-30-10]-001.mp4")
    datetime.datetime(2020, 3, 28, 13, 0, 10)
    >>> parse_str_to_date("test-[2020-03-28_12-30-10].mp4")
    datetime.datetime(2020, 3, 28, 12, 30, 10)
    >>> parse_str_to_date("test.mp4")
    None
    """
    match = re.compile(
        r"\[\d{4}(-\d{2}){2}_(\d{2}-){2}\d{2}\](-\d{3})?"
    ).search(string)

    if not match:
        logger.warning(f"no date found in str, {string}")
        return None

    try:
        # Offset is optional in the regex, (-\d{3})?. This tries to split on
        # "]-", which means there exist an offset, [<datetime>]-<offset>. If it
        # fails it means there are no offset.
        timestamp, offset = match[0].split("]-")

        # timestamp still has a "[" at the start. This strips it.
        timestamp = timestamp[1:]
        offset = int(offset)
    except ValueError:
        # No offset found, so only grab what's inside the brackets, and set
        # offset to zero.
        timestamp = match[0][1:-1]
        offset = 0

    date = "-".join(timestamp.split("_"))

    year, month, day, hour, minute, second = [int(x) for x in date.split("-")]

    try:
        return datetime(year, month, day, hour, minute, second) + timedelta(
            minutes=offset_min * offset
        )
    except ValueError:
        return None


def _get_video_metadata(path) -> Tuple[int, ...]:
    """Get metadata from video using `opencv`.

    Parameter
    ---------
    path : str
        path to file to get metadata from.

    Return
    ------
    Typle[int, int, int, int] :
        A tuple with the metadata:
        (height, width, FPS, frame_count)

    Raises
    ------
    FileNotFoundError:
        If the file can't be opened it will throw FileNotFoundError
    RuntimeError:
        If there are problems getting any metadata.
    """
    video = cv.VideoCapture(path)  # type: ignore

    if not video.isOpened():
        raise FileNotFoundError(f"Could not open {path}")

    metadata = (
        int(video.get(cv.CAP_PROP_FRAME_HEIGHT)),  # type: ignore
        int(video.get(cv.CAP_PROP_FRAME_WIDTH)),  # type: ignore
        int(video.get(cv.CAP_PROP_FPS)),  # type: ignore
        int(video.get(cv.CAP_PROP_FRAME_COUNT)),  # type: ignore
    )

    video.release()

    # Frame count becomes "-9223372036854775808" when testing with png. Opencv
    # should return 0 if it fails, but apparently not in this case...
    for meta in metadata:
        if meta < 1:
            raise RuntimeError(f"Could not get metadata for file {path}")

    return metadata


@dataclass
class Frame:
    """Simple dataclass representing frame."""

    idx: int
    detections: List[Detection]
    timestamp: Optional[datetime] = None

    def to_json(self) -> Dict[str, Any]:
        """Convert frame to json.

        Return
        ------
        Dict[str, Any] :
            Object as json:
            {
                "idx": int,
                "detections": List[Detection],
                "timestamp": None|str
            }

        """
        return {
            "idx": self.idx,
            "detections": [det.to_json() for det in self.detections if det],
            "timestamp": None
            if not self.timestamp
            else self.timestamp.isoformat(),
        }


@dataclass
class BBox:
    """Class representing a Bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Detection:
    """Class representing a Detection.

    Parameter
    ---------
    bbox: BBox
        A bounding box
    probaility: float
        Probability from detection
    label: int
        Class label from detection
    frame: int
        Which frame it belongs to

    Example
    -------
    >>> bbox = BBox(10,20,30,40)
    >>> detection = (bbox, 0.8, 1, 4)
    >>> print(detection)
    (BBox(x1=10, y1=20, x2=30, y2=40), 0.8, 1, 4)
    """

    bbox: BBox
    probability: float
    label: int
    frame: int

    def to_json(self) -> Dict[str, Any]:
        """Convert detection to json.

        Return
        ------
        Dict[str, Any] :
            Detection as json,
            {
                "bbox": BBox,
                "probability": float,
                "label": int,
                "frame": int,
            }

        """
        return {
            "bbox": asdict(self.bbox),
            "probability": self.probability,
            "label": self.label,
            "frame": self.frame,
        }

    def set_frame(self, frame: int) -> Detection:
        """Update frame nr.

        Returns itself so it can be used in list comprehensions.

        Parameter
        ---------
        frame : int
              The frame number the detection is found in.

        Return
        ------
        Detection :
                  Returns self.
        """
        self.frame = frame
        return self

    @classmethod
    def from_api(
        cls, bbox: Dict[Any, str], probability: float, label: int, frame: int
    ) -> Detection:
        """Create Detection class from tracker.

        Parameter
        ---------
        bbox: Dict[Any, str]
            Dict representation of BBox
        probaility: float
            Probability from detection
        label: int
            Class label from detection
        frame: int
            Which frame it belongs to
        Return
        ------
        Detection :
            A detection object
        """
        return cls(BBox(**bbox), probability, label, frame)


class Object:
    """Class representation of an object that has been detected and tracked."""

    def __init__(
        self, label: int, detections: List[Detection] = [], track_id: int = None
    ) -> None:
        """Create an Object.

        Parameters
        ----------
        label : int
            The label given to it by the tracker and detector
        detections  : List[Detection]
            List of detections accociated with this object. Default=[]
        track_id    : int
            Tracking ID for this object. Default=None
        """
        self.label: int = label
        self.probability: float = 0.0
        self._detections: List[Detection] = detections
        self.track_id: Optional[int] = track_id
        self.time_in: Optional[datetime] = None
        self.time_out: Optional[datetime] = None
        self._calc_label()

    def _calc_label(self) -> None:
        """Calculate label."""
        if len(self._detections) == 0:
            return

        self.label = int(
            np.bincount([detect.label for detect in self._detections]).argmax()
        )

        self.probability = sum(
            [
                detect.probability
                for detect in self._detections
                if detect.label == self.label
            ]
        ) / len(self._detections)

    @classmethod
    def from_api(
        cls, track_id: int, detections: List[Dict[Any, str]], label: int
    ) -> Object:
        """Create Object class from tracker.

        Parameter
        ---------
        track_id : int
            track_id from tracker
        detections : List[Dict[Any,str]]
            List of detections associated.
        label : int
            Class label

        Return
        ------
        Object :
            Fully featured Object.
        """
        dets = [Detection.from_api(**detect) for detect in detections]
        return cls(label, dets, track_id)

    def get_results(self) -> Dict[str, Any]:
        """Return information on this object.

        Return
        ------
        Dict[str, Any] :

        """
        self._calc_label()

        return {
            "track_id": self.track_id,
            "label": self.label,
            "probability": self.probability,
            "time_in": self.time_in,
            "time_out": self.time_out,
        }

    def __eq__(self, o: object) -> bool:
        """Check if two Objects are same.

        Currently, this doesn't do much, but in the future, it should implement to
        check detections as well.
        """
        return (
            isinstance(o, Object)
            and self.label == o.label
            and self.probability == o.probability
            and len(self._detections) == len(o._detections)
        )

    def add_detection(self, detection: Detection) -> None:
        """Add a detection to the object.

        Parameter
        ---------
        detection : Detection
        """
        self._detections.append(detection)
        self._calc_label()

    def number_of_detections(self) -> int:
        """Return the number of detections.

        Return
        ------
        int :
           Number of detections
        """
        return len(self._detections)

    def get_detection(self, idx: int) -> Optional[Detection]:
        """Return the detection at index idx.

        Parameter
        ---------
        idx: int
            Index

        Return
        ------
        Optional[Detection] :
            Detection at index idx or None if none found.
        """
        try:
            return self._detections[idx]
        except IndexError:
            return None


class Job:
    """Class representation of a job."""

    def __init__(
        self,
        name: str,
        description: str,
        location: str,
        status: Status = Status.PENDING,
    ) -> None:
        self.id: Optional[int] = None
        self.name: str = name
        self.description: str = description
        self._status: Status = status
        self._objects: List[Object] = list()
        self.videos: List[Video] = list()
        self.location: str = location

    def __hash__(self) -> int:
        """Hash of object used in eg. `set()` to avoid duplicate."""
        return hash(
            (type(self),)
            + (self.name, self.description, self.id, self.location)
        )

    def __eq__(self, other) -> bool:
        """Check if job is equal to another object."""
        if not isinstance(other, Job):
            return False
        # Note: Will not be able to check equality if jobs do not have `id`,
        # as this is the only unique parameter. A job without `id` is not
        # seen by `repository` before, so it is a new `job`.
        if self.id and other.id:
            return self.id == other.id
        return False

    def __repr__(self):
        """Override of default __repr__. Gives object representation as a string."""
        return str(self.__class__) + ": " + str(self.__dict__)

    def add_object(self, obj: Object) -> None:
        """Add an object to a job.

        Parameter
        ---------
        obj : Object
            An object to add
        """
        self._objects.append(obj)

    def number_of_objects(self) -> int:
        """Return number of objects.

        Return
        ------
        int :
            Number of objects
        """
        return len(self._objects)

    def get_object(self, idx: int) -> Optional[Object]:
        """Return object at index.

        Paramter
        --------
        idx : int
            Index in the list

        Return
        ------
        Optional[Object] :
            Object at index idx. If none are found, returns None.
        """
        try:
            return self._objects[idx]
        except IndexError:
            return None

    def get_result(self) -> List[Dict[str, Any]]:
        """Return result from all objects.

        Return
        ------
        List[Dict[str, Any]] :

        """
        return [obj.get_results() for obj in self._objects]

    def add_video(self, video: Video) -> bool:
        """Add a video to this job in order to be processed.

        Parameter
        ---------
        video   :   Video
            Video to add to this job. Must have a valid timestamp.

        Return
        ------
        bool    :
            True if video has a set timestamp, and is not already in the
            videos list. False otherwise.

        """
        if video.timestamp is None:
            logger.warning("Videos added to job must have set timestamp.")
            return False

        if video in self.videos:
            logger.warning("Attempted to add an existing video to a job.")
            return False

        self.videos.append(video)
        self.videos.sort(key=lambda x: x.timestamp.timestamp())
        return True

    def add_videos(self, videos: List[Video]) -> bool:
        """Add a list of videos to this job in order to be processed.

        Parameter
        ---------
        videos  :   List[Video]
            List of videos to add. All must have a valid timestamp.

        Return
        ------
        bool    :
            True if all videos in the list has a timestamp, false otherwise.
            No videos gets added if False is returned.
        """
        for video in videos:
            if video in self.videos:
                logger.warning("Video has already been added to the job.")
                return False

            if video.timestamp in [v.timestamp for v in videos if v != video]:
                logger.warning("Duplicate timestamp.")
                return False

        for video in videos:
            self.videos.append(video)

        self.videos.sort(key=lambda x: x.timestamp.timestamp())
        return True

    def remove_video(self, video: Video) -> bool:
        """Remove an existing video from this job.

        Parameter
        ---------
        video   :   Video
            video to remove from the job.

        Return
        ------
        bool    :
            True if the video was removed from the job. False otherwise.
        """
        if video in self.videos:
            self.videos.remove(video)
            return True
        else:
            return False

    def total_frames(self) -> int:
        """Get the total frames in all videos for this job.

        Return
        ------
        int     :
            Ammount of frames in total over all video objects in this job.
        """
        return sum([v.frames for v in self.videos])

    def status(self) -> Status:
        """Get the job status for this job."""
        return self._status

    def start(self) -> None:
        """Mark the job as started."""
        if self._status is Status.DONE or self._status is Status.RUNNING:
            raise JobStatusException
        logger.debug("Job '%s' starting", self.name)
        self._status = Status.RUNNING

    def pause(self) -> None:
        """Mark the job as paused."""
        if self._status is not Status.RUNNING:
            raise JobStatusException
        logger.debug("Job '%s' paused", self.name)
        self._status = Status.PAUSED

    def complete(self) -> None:
        """Mark the job as completed."""
        if self._status is not Status.RUNNING:
            raise JobStatusException
        logger.debug("Job '%s' marked as completed", self.name)
        self._status = Status.DONE

    def queue(self) -> None:
        """Mark the job as queued."""
        if self._status is not Status.PENDING:
            raise JobStatusException
        logger.debug("Job '%s' marked as queued", self.name)
        self._status = Status.QUEUED


class JobStatusException(Exception):
    """Exception when job attempt to change into invalid state."""

    pass


class Project:
    """Project class.

    Top level abstraction for organisation of jobs connected to specified
    projects.

    Parameters
    ----------
    id      :   int
            Project internal id number
    name    :   str
            Project name
    number  :   str
            A unique project number. This number is a reference to external
            reference number used by the user.
    location    :   str
            Optional string representing the location for this project.
    description :   str
                    Project description.

    Attribute
    ---------
    number_of_jobs  :   int
                        Number of jobs associated with project.

    Methods
    -------
    add_job(job: Job)
        Adds a new job to project. No duplicates allowed.
    remove_job(number: str)
        Removes job from project.
    list_jobs()
        Returns a list of associated _jobs_.
    """

    def __init__(
        self,
        name: str,
        number: str,
        description: str,
        location: Optional[str] = None,
    ) -> None:
        self.id: int
        self.name: str = name
        self.number: str = number
        self.description: str = description
        self.location: Optional[str] = location
        self.jobs: List[Job] = list()

    def __str__(self):
        """Print class members."""
        return f"Name: {self.name}, Description: {self.description}"

    def __eq__(self, other) -> bool:
        """Check equality between objects.

        Operator used in tests to check if objects from DB is correct.
        """
        if not isinstance(other, Project):
            return False
        return (
            other.id == self.id
            and other.name == self.name
            and other.description == self.description
            and other.number == self.number
            and other.location == self.location
        )

    def __hash__(self) -> int:
        """Hash of object used in eg. `dict()` or `set()` to avoid duplicate."""
        return hash((type(self),) + tuple(self.__dict__))

    def __repr__(self):
        """Override of default __repr__. Gives object representation as a string."""
        return (
            str(self.__class__) + ": " + str(self.__dict__)
        )  # pragma: no cover

    @classmethod
    def from_dict(cls, project_data: dict) -> Project:
        """Only an example method of a "named constructor"."""
        return cls(
            name=project_data["name"],
            number=project_data["number"],
            description=project_data["description"],
            location=project_data["location"],
        )

    @property
    def number_of_jobs(self) -> int:
        """Get number of jobs associated with project.

        Returns
        -------
        int
            Number of jobs in project
        """
        return len(self.jobs)

    def add_job(self, job: Job) -> Project:
        """Add job to project.

        Parameter
        ---------
        job     :   Job
                    Job to be added to project.
        """
        if job in self.jobs:
            logger.debug(
                "Attempted to add existing job '%s' to a project", job.name
            )
        else:
            logger.debug("Added job '%s' to project", job.name)
            self.jobs.append(job)
        return self

    def get_jobs(self):
        """Retrieve all jobs from the project.

        Returns
        -------
         :  List[Job]
            List containing all jobs within the project
        """
        return self.jobs

    def get_job(self, job_id: int) -> Optional[Job]:
        """Retrive a single job from the project.

        Parameters
        ----------
        job_id : int
            Index of the job we seek. 0 is not valid.

        Returns
        -------
        Job
            The job object if found.
        """
        for job in self.jobs:
            if job.id == job_id:
                return job

        return None

    def remove_job(self, job: Job) -> bool:
        """Remove job from project.

        Parameters
        ----------
        job     :   Job
                    Job to be removed.

        Returns
        -------
        bool
            True if the job was successfully removed
        """
        if job in self.jobs:
            self.jobs.remove(job)
            logger.debug("Removed job with name '%s' from a project", job.name)
            return True
        else:
            logger.debug(
                "Could not find job with name '%s' to remove in project",
                job.name,
            )
            return False
