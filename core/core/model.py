"""Module defining the domain model entities."""
from __future__ import annotations

import logging
import os.path
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import ffmpeg
import numpy as np

import core

logger = logging.getLogger(__name__)


class Status(str, Enum):
    """Enum for job progress."""

    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    DONE = "Done"


class Video:
    """Video class.

    This class provides various functions to retrieve data from a video file.

    Parameters
    ----------
    path    :   str
            Path to this video file as a string
    frames  :   int
            Number of frames in the video
    fps     :   int
            Frames per second in the video
    width   :   int
            Width in pixels
    height  :   int
            Height in pixels

    Attribute
    ---------
    _path   :   str
            Path to the video file associated with the video.
    frames  :   int
            Number of frames in the video
    fps     :   int
            Frames per second in the video
    width   :   int
            Width in pixels
    height  :   int
            Height in pixels

    Methods
    -------
    exists()
        Checks if the path is valid, by checking if its a file on the disk.
    from_path(path: str)
        Named constructor that creates and populates a video object with
        metadata read from the file. Raises FileNotFoundError if the
        file could not be read, or is not a video file.

    Examples
    --------
    >>> video = Video.from_path("test.mp4")
    >>> one_frame = video[5]
    >>> print(one_frame.shape)
    (720, 1280, 3)
    >>> many_frames = video[5,10]
    >>> print(many_frames.shape)
    (5, 720, 1280, 3)

    Raises
    ------
    FileNotFoundError
        If error reading video file when creating `from_path()`.
    """

    def __init__(
        self, path: str, frames: int, fps: int, width: int, height: int
    ) -> None:
        self._path: str = path
        self.frames: int = frames
        self.fps: int = fps
        self.width: int = width
        self.height: int = height
        self.timestamp = parse_str_to_date(self._path)

    def __get__(self, key) -> np.ndarray:
        """Get one frame of video.

        Used by `__getitem__` when only one key is given.

        Returns
        -------
        numpy.ndarray
            One frame of video as `ndarray`.
        """
        if key < 0 or key >= self.frames:
            raise IndexError

        # ffmpeg filter docs:
        # http://ffmpeg.org/ffmpeg-filters.html#select_002c-aselect
        frame, _ = (
            ffmpeg.input(self._path)
            .filter("select", "gte(n, {})".format(key))
            .output("pipe:", vframes=1, format="rawvideo", pix_fmt="rgb24")
            .run(capture_stdout=True)
        )
        return np.frombuffer(frame, np.uint8).reshape(
            [self.height, self.width, 3]
        )

    def __getitem__(self, interval: slice):
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

        """
        # If only one key is given
        if type(interval) == int:
            return self.__get__(interval)

        if interval.stop > self.frames and interval.start >= 0:
            raise IndexError

        # Slice stepping is not implemented.
        if interval.step != None:
            raise NotImplementedError

        numbers = interval.stop - interval.start

        # ffmpeg filter docs:
        # http://ffmpeg.org/ffmpeg-filters.html#select_002c-aselect
        frame, _ = (
            ffmpeg.input(self._path)
            .filter(
                "select",
                "between(n,{},{})".format(interval.start, interval.stop),
            )
            .output(
                "pipe:", vframes=numbers, format="rawvideo", pix_fmt="rgb24"
            )
            .run(capture_stdout=True)
        )
        return np.frombuffer(frame, np.uint8).reshape(
            [-1, self.height, self.width, 3]
        )

    def exists(self) -> bool:
        """Check if the file path is a valid file."""
        return os.path.isfile(self._path)

    @classmethod
    def from_path(cls, path: str) -> Video:
        """Named constructor to create a `Video` from path.

        Examples
        --------
        >>> video = Video.from_path("video.mp4")
        >>> type(video)
        <class 'core.model.Video'>
        """
        height, width, fps, frame_numbers = _get_video_metadata(path)

        return cls(
            path=path,
            frames=frame_numbers,
            fps=fps,
            width=width,
            height=height,
        )

    def timestamp_at(self, idx: int) -> datetime:
        """Return timestamp at index in video.

        Parameter
        ---------
        idx : int

        Return
        ------
        datetime :

        """
        if idx > self.frames:
            raise IndexError
        if idx < 0:
            raise IndexError

        return self.timestamp + (timedelta(seconds=int(idx / self.fps)))


def parse_str_to_date(path: str) -> Optional[datetime]:
    """Parse string to date.

    Parameter
    ---------
    path: str
        string to parse to date on the format:
        `[yyyy-mm-dd_hh-mm-ss]`


    Return
    ------
    datetime :
        parsed datetime object, or None if unsuccessfull

    """
    date = re.compile(r"\[\d{4}(-\d{2}){2}_(\d{2}-){2}\d{2}\]").search(path)

    if not date:
        logger.error(f"no date found in path, {path}")
        return None

    date_temp = date[0][1:-1].split("_")

    year, month, day, hour, minute, second = [
        int(x) for x in date_temp[0].split("-") + date_temp[1].split("-")
    ]

    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


def _get_video_metadata(path) -> Tuple[int, ...]:
    """Get metadata from video using `ffmpeg`."""
    try:
        probe = ffmpeg.probe(path)
        video_info = next(
            s for s in probe["streams"] if s["codec_type"] == "video"
        )
        return (
            int(video_info["height"]),
            int(video_info["width"]),
            int(video_info["r_frame_rate"].split("/")[0]),
            int(video_info["nb_frames"]),
        )
    except ffmpeg.Error as e:
        logger.error(
            "Unable to get video metadata from %s. Error: %s", path, e.stderr
        )
        raise FileNotFoundError


@dataclass
class Frame:
    """Simple dataclass representing frame."""

    idx: int
    detections: List[Detection]
    timestamp: Optional[datetime] = None


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

    def __init__(self, label: int) -> None:
        """Create an Object.

        Parameters
        ----------
        label : int
            The label given to it by the tracker and detector
        """
        self.label: int = label
        self.probability: float = 0.0
        self._detections: list[Detection] = list()
        self.track_id: int
        self.time_in = datetime(1, 1, 1)
        self.time_out = datetime(1, 1, 1)
        self._calc_label()

    def _calc_label(self) -> None:
        """Calculate label."""
        if len(self._detections) == 0:
            return

        self.label = np.bincount(
            [detect.label for detect in self._detections]
        ).argmax()

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
        obj = cls(label)
        obj._detections = [
            Detection.from_api(**detect) for detect in detections
        ]
        obj.track_id = track_id

        return obj

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
        self, name: str, description: str, status: Status = Status.PENDING
    ) -> None:
        self.id: Optional[int] = None
        self.name: str = name
        self.description: str = description
        self._status: Status = status
        self._objects: List[Object] = list()
        self.videos: List[Video] = list()

    def __hash__(self) -> int:
        """Hash of object used in eg. `set()` to avoid duplicate."""
        return hash((type(self),) + (self.name, self.description, self.id))

    def __eq__(self, other) -> bool:
        """Check if job is equal to another object."""
        if not isinstance(other, Job):
            return False
        if self.id and other.id:
            return (
                self.name == other.name
                and self.description == other.description
                and self.id == other.id
            )
        return self.name == other.name and self.description == other.description

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

    def add_video(self, video: Video) -> bool:
        """Add a video to this job in order to be processed."""
        raise NotImplementedError

    def remove_video(self, video_id: int) -> bool:
        """Remove an existing video from this job."""
        raise NotImplementedError

    def list_videos(self) -> List[Video]:
        """Retrieve a list of all videos in this job."""
        raise NotImplementedError

    def _process_job(self) -> None:
        raise NotImplementedError
        frames: List[Frame] = list()

        for video in self.videos:
            # frames = interface.detector.predict(Video[start:end])
            for frame in frames:
                frame.timestamp = video.timestamp_at(frame.idx)

        objects = core.interface.to_track(frames)
        if objects:
            self._objects = objects

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
        self._jobs: Set[Job] = set()

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
        return hash((type(self),) + tuple(self.__dict__.values()))

    def __repr__(self):
        """Override of default __repr__. Gives object representation as a string."""
        return str(self.__class__) + ": " + str(self.__dict__)

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
        return len(self._jobs)

    def add_job(self, job: Job) -> Project:
        """Add job to project.

        Parameter
        ---------
        job     :   Job
                    Job to be added to project.
        """
        if job in self._jobs:
            logger.debug(
                "Attempted to add existing job '%s' to a project", job.name
            )
        else:
            logger.debug("Added job '%s' to project", job.name)
            self._jobs.add(job)
        return self

    def get_jobs(self):
        """Retrieve all jobs from the project.

        Returns
        -------
         :  List[Job]
            List containing all jobs within the project
        """
        return list(self._jobs)

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
        for job in self._jobs:
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
        if job in self._jobs:
            self._jobs.remove(job)
            logger.debug("Removed job with name '%s' from a project", job.name)
            return True
        else:
            logger.debug(
                "Could not find job with name '%s' to remove in project",
                job.name,
            )
            return False


class Scheduler:
    """Scheduler to orchestrate jobs across projects."""

    def __init__(self) -> None:
        self._jobs = set()  # type: Set[Job]

    def add_job(self, job: Job) -> None:
        """Add a job to the scheduler to be processed."""
        self._jobs.add(job)
