"""Pydantic shema of object recived and sent on API."""
from datetime import datetime
from typing import Any, Optional

from pydantic import Field, field_validator, ConfigDict, BaseModel

from core import model
from core.model import Detection


def get_label(label_id: int) -> str:
    """Convert a object label id into a str."""
    if not isinstance(label_id, int):
        raise TypeError(f"expected type int, got type {type(label_id)}")
    # TODO: This should get labels from `interface.Detector()' object,
    # however tests need to be refactored since `Detector` need detection
    # api. For now the labels are stored in a list.
    # model = interface.Detector().available_models[0]
    available_labels = [
        "Gjedde",
        "Gullbust",
        "Rumpetroll",
        "Stingsild",
        "Ørekyt",
        "Abbor",
        "Brasme",
        "Mort",
        "Vederbuk",
    ]

    if label_id > len(available_labels):  # pragma: no cover
        return "Unknown label"

    return available_labels[label_id]


class HashableBaseModel(BaseModel):  # pragma: no cover
    """Custom definition of `BaseModel` who implements `__hash__`."""

    def __hash__(self) -> int:
        """Hash member variables values."""
        return hash((type(self),) + tuple(self.__dict__.values()))


class Object(BaseModel):
    """Base model for `Object` class used in API."""

    id: int
    label: str
    probability: float
    detections: dict[str, list[float]] = Field(alias="_detections")
    time_in: datetime
    time_out: datetime
    video_ids: list[int]
    model_config = ConfigDict(from_attributes=True)

    @field_validator("label", mode="before")
    @classmethod
    def convert_label(cls, label_id: int) -> str:
        """Convert object label from id to str."""
        return get_label(label_id)

    @field_validator("detections", mode="before")
    @classmethod
    def convert_detection(
        cls, _detections: list[Detection]
    ) -> dict[str, list[float]]:
        """Convert detections to Dict."""
        detections: dict[str, list[float]] = dict()
        for d in _detections:
            if get_label(d.label) not in detections:
                detections[get_label(d.label)] = list()

            detections[get_label(d.label)].append(d.probability)
        return detections


class Video(BaseModel):
    """Video class used in API."""

    id: int
    path: str = Field(alias='_path')
    frame_count: int
    timestamp: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobBase(HashableBaseModel):
    """Base model for `Job` class used in API."""

    name: str
    description: str
    location: str


class JobStat(BaseModel):
    """Base class for Jobs that need stats."""

    total_objects: int
    total_labels: int
    labels: dict[str, int] = dict()

    @field_validator("labels", mode="before")
    @classmethod
    def convert_labels(cls, labels_dict: dict[int, int]) -> dict[str, int]:
        """Convert labels with ints to identify labels to their respective strings."""
        labels = {}
        for (label_id, count) in labels_dict.items():
            if not isinstance(label_id, str):
                labels[get_label(int(label_id))] = count
            else:
                labels[label_id] = count
        return labels


class JobBare(JobBase):
    """Bare model for a Job."""

    id: int
    status: model.Status
    video_count: int
    progress: int
    stats: JobStat

    @field_validator("stats", mode="before")
    @classmethod
    def convert_stats(cls, stats_dict: dict[str, Any]) -> JobStat:
        """Convert dictionary stats to JobStats."""
        return JobStat(**stats_dict)


class Job(JobBase):
    """`Job` class used to send object on API."""

    id: int
    status: model.Status = Field(alias='_status')
    location: str
    videos: list[Video] = []
    progress: int
    stats: JobStat
    model_config = ConfigDict(from_attributes=True)

    @field_validator("stats", mode="before")
    @classmethod
    def convert_stats(cls, stats_dict: dict[str, Any]) -> JobStat:
        """Convert dictionary stats to JobStats."""
        return JobStat(**stats_dict)

    def __hash__(self) -> int:
        """Hash status data in job."""
        return hash((type(self),) + (self.name, self.description, self.id))


class JobCreate(JobBase):
    """Class for new Job received on API."""

    videos: list[str]


class ProjectBase(HashableBaseModel):
    """Base model for `Project` class used in API."""

    name: str
    number: str
    description: str
    location: Optional[str] = None


class ProjectBare(ProjectBase):
    """Bare model for `Project` that don't hold a list of jobs."""

    id: int
    job_count: int


class Project(ProjectBase):
    """`Project` class used to send object on API."""

    id: int
    jobs: list[Job] = []
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(ProjectBase):
    """Class for new `Project` received on API."""
