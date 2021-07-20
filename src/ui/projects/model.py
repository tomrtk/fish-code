"""Collection of classes that fullfills the mocking."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class Object:
    """Holds the combined detection into an object."""

    id: int
    label: str
    probability: float
    time_in: datetime
    time_out: datetime
    _detections: dict[str, list[float]]
    video_ids: list[int]

    @classmethod
    def from_dict(cls, object_data: dict[str, Any]) -> Object:
        """Return a new object from a dict."""
        return cls(
            id=object_data["id"],
            label=object_data["label"],
            time_in=datetime.fromtimestamp(object_data["label"]),
            time_out=datetime.fromtimestamp(object_data["label"]),
            probability=object_data["probability"],
            _detections=object_data["_detections"],
            video_ids=object_data["video_ids"],
        )


@dataclass
class JobBase:
    """Holds the base data of a Job."""

    name: str
    description: str
    location: str


@dataclass
class JobBare(JobBase):
    """Holds the base data of a Job."""

    _status: str
    video_count: int
    progress: int
    id: int | None = None
    project_id: int | None = None
    project_name: str | None = None
    stats: dict[str, Any] | None = None

    @classmethod
    def from_dict(
        cls, job_data: dict[str, Any], project_id: int, project_name: str
    ) -> JobBare:
        """Create job from dict data."""
        return cls(
            _status=job_data["status"],
            description=job_data["description"],
            id=job_data["id"],
            location=job_data["location"],
            name=job_data["name"],
            project_id=project_id,
            project_name=project_name,
            progress=job_data["progress"],
            video_count=job_data["video_count"],
            stats=job_data["stats"],
        )


@dataclass
class Job(JobBase):
    """Hold the job details."""

    _status: str
    videos: list[str]
    id: int | None = None
    project_id: int | None = None
    project_name: str | None = None
    progress: int | None = None
    stats: dict[str, Any] | None = None

    def to_post_dict(self) -> dict[str, str | list[str]]:
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
        cls, job_data: dict[str, Any], project_id: int, project_name: str
    ) -> Job:
        """Create job from dict data."""
        return cls(
            _status=job_data["_status"],
            description=job_data["description"],
            id=job_data["id"],
            location=job_data["location"],
            name=job_data["name"],
            project_id=project_id,
            project_name=project_name,
            videos=job_data["videos"],
            progress=job_data["progress"],
            stats=job_data["stats"],
        )

    def get_object_stats(self) -> dict[str, Any] | None:
        """Return total stat for all objects inside the job."""
        return self.stats


@dataclass
class Project:
    """Hold the project details."""

    description: str
    name: str
    location: str
    number: str
    owner: str | None = None
    id: int | None = None
    date: str | None = None
    jobs: list[Job] | None = None

    def get_job_count(self) -> int:
        """Get the count of jobs inside the project."""
        if not self.jobs:
            return 0

        return len(self.jobs)

    def get_name(self) -> str:
        """Return the projects name."""
        return self.name

    def to_post_dict(self) -> dict[str, str]:
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
    def from_dict(cls, project_data: dict[str, Any]) -> Project:
        """Convert text to a new Project object."""
        project_jobs: list[Job] = list()

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

    def get_name(self) -> str:
        """Return the project's name."""
        return self.name

    def get_job_count(self) -> int:
        """Return the job count."""
        return self.job_count


@dataclass
class Projects:
    """Hold the projects."""

    projects: list[Project]


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
    frame_count: int
    timestamp: datetime
