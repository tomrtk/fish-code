"""Collection of classes that fullfills the mocking."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Job:
    """Hold the job details."""

    name: str
    description: str
    _status: str
    videos: List[str]
    id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    progress: Optional[int] = None
    _objects: Optional[Any] = None

    def to_json(self) -> str:
        """Return JSON."""
        return json.dumps(
            {
                "name": self.name,
                "description": self.description,
            }
        )

    def get_status(self) -> str:
        """Return status as proper."""
        return self._status.lower()

    @classmethod
    def from_dict(
        cls, job_data: Dict[str, Any], project_id: int, project_name: str
    ) -> Job:
        """Create job from dict data."""
        return cls(
            project_id=project_id,
            project_name=project_name,
            id=job_data["id"],
            name=job_data["name"],
            description=job_data["description"],
            _status=job_data["_status"],
        )


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

    def job_count(self) -> int:
        """Get the count of jobs inside the project."""
        if not self.jobs:
            return 0

        return len(self.jobs)

    def get_name(self) -> str:
        """Return the projects name."""
        return self.name

    def to_json(self) -> str:
        """Convert boundingbox to dict.

        Return
        ------
        Dict[str, float] :
            {"x1": float, "y1": float, "x2": float, "y2": float}
        """
        return json.dumps(
            {
                "name": self.name,
                "number": self.number,
                "description": self.description,
            }
        )

    @classmethod
    def from_dict(cls, project_data: Dict[str, Any]) -> Project:
        """Convert text to a new Project object."""
        project_jobs: List[Job] = list()

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
    video_path: str
