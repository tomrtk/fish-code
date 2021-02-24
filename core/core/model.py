""" Module defining the domain model entities.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

logger = logging.getLogger(__name__)


class Status(str, Enum):
    """Enum for job progress."""

    PENDING = "Pending"
    RUNNING = "Running"
    DONE = "Done"


class Video:
    """TODO"""

    def __init__(self) -> None:
        pass


class Job:
    """TODO"""

    def __init__(self, id: int, name: str) -> None:
        self.id: int = id
        self.name: str = name
        self._status: Status = Status.PENDING

    def __hash__(self) -> int:
        """Hash of object used in eg. `set()` to avoid duplicate."""
        return hash((self.id, self.name))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Job):
            return False
        return self.name == other.name and self.id == other.id

    @property
    def progress(self) -> int:
        # TODO: Calculate progress from number of frames completed in associated videos.
        import random

        return random.randrange(0, 100, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self._status.value,
            "progress": self.progress,
        }

    def add_video(self, video: Video) -> bool:
        raise NotImplementedError

    def remove_video(self, video_id: int) -> bool:
        raise NotImplementedError

    def list_videos(self) -> List[Video]:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class Project:
    """Project class.

    Top level abstraction for organisation of jobs connected to specified
    projects.

    Parameters
    ----------
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
        self.jobs: Dict[int, Job] = dict()

    def __str__(self):
        """Print class members."""
        return f"Name: {self.name}, Number: {self.number}, Description: {self.description}"

    def __eq__(self, other) -> bool:
        """Check equality between objects.

        Operator used in tests to check if objects from DB is correct.
        """
        if not isinstance(other, Project):
            return False
        # number is unique in db
        return (
            other.number == self.number
            and other.name == self.name
            and other.description == self.description
        )

    def __hash__(self) -> int:
        """Hash of object used in eg. `dict()` or `set()` to avoid duplicate."""
        return hash(
            (self.name, self.number, self.description, frozenset(self.jobs))
        )

    @classmethod
    def from_dict(cls, project_data: dict) -> Project:
        """Only an example method of a "named constructor"."""
        return cls(
            id=project_data["id"],
            name=project_data["name"],
            number=project_data["number"],
            description=project_data["description"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Only an example method of a "named constructor"."""
        return {
            "name": self.name,
            "number": self.number,
            "description": self.description,
            "jobs": self.jobs,
        }

    @property
    def number_of_jobs(self) -> int:
        """Get number of jobs associated with project.

        Returns
        -------
            :   int
                Number of jobs in project.
        """
        return len(self.jobs)

    def add_job(self, job: Job) -> None:
        """Add job to project.

        Parameter
        ---------
        job     :   Job
                    Job to be added to project.
        """
        if job.id in self.jobs.keys():
            logger.log(
                logging.INFO, f"Attempted to add job with existing ID: {job.id}"
            )
        else:
            self.jobs[job.id] = job

    def remove_job(self, id: int) -> bool:
        """Remove job from project

        Parameters
        ----------
        id      :   int
                    Job id of job to be removed.

        Returns
        -------
        bool
            True if the job was successfully removed
        """
        if id in self.jobs.keys():
            del self.jobs[id]
            return True
        else:
            return False

    def get_job(self, id: int) -> Optional[Job]:
        """Retrieve job from project

        Parameters
        ----------
        id  :   int
            ID of the job to be retrieved from the project

        Returns
        -------
        Optional[Job]
            Optional of type Job associated with the id
        """
        if id in self.jobs.keys():
            return self.jobs[id]
        else:
            return None

    def get_jobs(self) -> list[Job]:
        return list(self.jobs.values())


class Scheduler:
    def __init__(self) -> None:
        self._jobs = set()  # type: Set[Job]

    def add_job(self, job: Job) -> None:
        self._jobs.add(job)
