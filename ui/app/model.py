from dataclasses import dataclass
from typing import List


@dataclass
class Job:
    progress: int
    name: str
    status: str


@dataclass
class Project:
    description: str
    name: str
    number: str
    jobs: List[Job]


@dataclass
class Projects:
    projects: List[Project]


@dataclass
class Detection:
    id: int
    report_type: str
    start: int
    stop: int
    video_path: str


@dataclass
class Video:
    id: int
    location: str
    status: str
    video_path: str
