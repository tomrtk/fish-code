"""Collection of classes that fullfills the mocking."""
import json
from dataclasses import dataclass
from typing import List


@dataclass
class Job:
    """Hold the job details."""

    progress: int
    name: str
    status: str


@dataclass
class Project:
    """Hold the project details."""

    description: str
    name: str
    number: str

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
