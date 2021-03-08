"""Module defining the domain model entities."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class Status(str, Enum):
    """Enum for job progress."""

    PENDING = "Pending"
    RUNNING = "Running"
    PAUSED = "Paused"
    DONE = "Done"


class Video:
    """TODO."""

    def __init__(self) -> None:
        pass


@dataclass
class BBox:
    """Class representing a Bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class Detection:
    """Class representing a Detection."""

    bbox: BBox
    score: float
    label: int
    frame: int


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

    def __hash__(self) -> int:
        """Hash of object used in eg. `set()` to avoid duplicate."""
        return hash((type(self),) + (self.name, self.description, self.id))

    def __eq__(self, other) -> bool:
        """Check if job is equal to another object."""
        if not isinstance(other, Job):
            return False
        if self.id:
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

    def status(self) -> Status:
        """Get the job status for this job."""
        return self._status

    def start(self) -> None:
        """Mark the job as started."""
        logger.debug("Job '%s' starting", self.name)
        self._status = Status.RUNNING

    def pause(self) -> None:
        """Mark the job as paused."""
        logger.debug("Job '%s' paused", self.name)
        self._status = Status.PAUSED

    def complete(self) -> None:
        """Mark the job as completed."""
        logger.debug("Job '%s' marked as completed", self.name)
        self._status = Status.DONE


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

    def __init__(self, name: str, number: str, description: str) -> None:
        self.id: int
        self.name: str = name
        self.number: str = number
        self.description: str = description
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
