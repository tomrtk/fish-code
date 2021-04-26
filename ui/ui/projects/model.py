"""Collection of classes that fullfills the mocking."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class Object:
    """Holds the combined detection into an object."""

    label: str
    probability: float
    track_id: int
    time_in: datetime
    time_out: datetime
    _detections: Dict[str, List[float]]

    @classmethod
    def from_dict(cls, object_data: Dict[str, Any]):
        """Return a new object from a dict."""
        return cls(
            label=object_data["label"],
            track_id=object_data["track_id"],
            time_in=datetime.fromtimestamp(object_data["label"]),
            time_out=datetime.fromtimestamp(object_data["label"]),
            probability=object_data["probability"],
            _detections=object_data["_detections"],
        )


@dataclass
class Job:
    """Hold the job details."""

    name: str
    description: str
    _status: str
    videos: List[str]
    location: str
    _objects: List[Object]
    id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    progress: Optional[int] = None

    def to_post_dict(self) -> Dict[str, Union[str | List[str]]]:
        """Return prepared dict for posting.

        Return
        ------
        Dict[str, str] :
            Job ready to be submitted via the API.
        """
        return {
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "videos": self.videos,
        }

    def get_status(self) -> str:
        """Return status as proper."""
        return self._status.lower()

    @classmethod
    def from_dict(
        cls, job_data: Dict[str, Any], project_id: int, project_name: str
    ) -> Job:
        """Create job from dict data."""
        job_objects: List[Object] = list()

        for job_object in list(job_data["_objects"]):
            job_objects.append(Object(**job_object))

        return cls(
            _status=job_data["_status"],
            description=job_data["description"],
            id=job_data["id"],
            location=job_data["location"],
            name=job_data["name"],
            project_id=project_id,
            project_name=project_name,
            videos=job_data["videos"],
            _objects=job_objects,
            progress=job_data["progress"],
        )

    def get_object_stats(self) -> Dict[int, int]:
        """Return total stat for all objects inside the job."""
        object_count = dict()

        for obj in self._objects:
            res = object_count.get(obj.label)
            if not res:
                object_count[obj.label] = 1
            else:
                object_count[obj.label] += 1

        return object_count


@dataclass
class Project:
    """Hold the project details."""

    description: str
    name: str
    location: str
    number: str
    owner: Optional[str] = None
    id: Optional[int] = None
    date: Optional[str] = None
    jobs: Optional[List[Job]] = None

    def get_job_count(self) -> int:
        """Get the count of jobs inside the project."""
        if not self.jobs:
            return 0

        return len(self.jobs)

    def get_name(self) -> str:
        """Return the projects name."""
        return self.name

    def to_post_dict(self) -> Dict[str, str]:
        """Return prepared dict for posting.

        Return
        ------
        Dict[str, str] :
            Project ready to be submitted via the API.
        """
        return {
            "name": self.name,
            "number": self.number,
            "description": self.description,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, project_data: Dict[str, Any]) -> Project:
        """Convert text to a new Project object."""
        project_jobs: List[Job] = list()

        if "jobs" in project_data:
            for job in list(project_data["jobs"]):
                project_jobs.append(Job(**job))

        return cls(
            id=project_data["id"],
            name=project_data["name"],
            number=project_data["number"],
            description=project_data["description"],
            location=project_data["location"],
            jobs=project_jobs,
        )


@dataclass
class ProjectBare:
    """Hold the bare project.

    This is a class made to not include jobs.  Mostly to lower data when
    getting a project.
    """

    id: int
    name: str
    location: str
    description: str
    number: str
    job_count: int

    def get_name(self):
        """Return the project's name."""
        return self.name

    def get_job_count(self):
        """Return the job count."""
        return self.job_count


@dataclass
class Projects:
    """Hold the projects."""

    projects: List[Project]


@dataclass
class Detection:
    """Hold the detection details."""

    id: int
    report_type: str
    start: int
    stop: int
    video_path: str


@dataclass
class Video:
    """Hold the video details."""

    id: int
    location: str
    status: str
    _path: str
    frames: int
    timestamp: datetime
