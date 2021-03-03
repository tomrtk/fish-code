"""Collection of classes that fullfills the mocking."""
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
    jobs: List[Job]


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
