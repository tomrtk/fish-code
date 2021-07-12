"""Pydantic shema of object recived and sent on API."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

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
    detections: Dict[str, List[float]]
    time_in: datetime
    time_out: datetime
    video_ids: List[int]

    @validator("label", pre=True)
    def convert_label(cls, label_id: int) -> str:
        """Convert object label from id to str."""
        return get_label(label_id)

    @validator("detections", pre=True)
    def convert_detection(
        cls, _detections: List[Detection]
    ) -> Dict[str, List[float]]:
        """Convert detections to Dict."""
        detections: Dict[str, List[float]] = dict()
        for d in _detections:
            if get_label(d.label) not in detections:
                detections[get_label(d.label)] = list()

            detections[get_label(d.label)].append(d.probability)
        return detections

    class Config:
        """Pydantic configuration options."""

        fields = {"detections": "_detections"}
        orm_mode = True


class Video(BaseModel):
    """Video class used in API."""

    id: int
    path: str
    frame_count: int
    timestamp: Optional[datetime]

    class Config:
        """Pydantic configuration options."""

        orm_mode = True
        fields = {"path": "_path"}
        underscore_attrs_are_private = False


class JobBase(HashableBaseModel):
    """Base model for `Job` class used in API."""

    name: str
    description: str
    location: str


class JobStat(BaseModel):
    """Base class for Jobs that need stats."""

    total_objects: int
    total_labels: int
    labels: Dict[str, int] = dict()

    @validator("labels", pre=False)
    def convert_labels(cls, labels_dict: Dict[Any, int]) -> Dict[str, int]:
        """Convert labels with ints to identify labels to their respective strings."""
        try:
            labels = {
                get_label(int(label_id)): count
                for (label_id, count) in labels_dict.items()
            }
        except ValueError:
            # Some edgecase causes FastAPI to do this twice. If every key is of
            # type `str` then we assume they have a valid label.
            if True in [not isinstance(k, str) for k in labels_dict.keys()]:
                raise TypeError("Expected every element to be of type str.")
            return labels_dict
        else:
            return labels


class JobBare(JobBase):
    """Bare model for a Job."""

    id: int
    status: model.Status
    video_count: int
    progress: int
    stats: JobStat

    @validator("stats", pre=True)
    def convert_stats(cls, stats_dict: Dict[str, Any]) -> JobStat:
        """Convert dictionary stats to JobStats."""
        return JobStat(**stats_dict)


class Job(JobBase):
    """`Job` class used to send object on API."""

    id: int
    status: model.Status
    location: str
    videos: List[Video] = []
    progress: int
    stats: JobStat

    @validator("stats", pre=True)
    def convert_stats(cls, stats_dict: Dict[str, Any]) -> JobStat:
        """Convert dictionary stats to JobStats."""
        return JobStat(**stats_dict)

    def __hash__(self) -> int:
        """Hash status data in job."""
        return hash((type(self),) + (self.name, self.description, self.id))

    class Config:
        """Pydantic configuration options."""

        orm_mode = True
        fields = {"status": "_status", "objects": "_objects"}
        underscore_attrs_are_private = False
        use_enum_values = True


class JobCreate(JobBase):
    """Class for new Job received on API."""

    videos: List[str]


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
    jobs: List[Job] = []

    class Config:
        """Pydantic configuration options."""

        orm_mode = True


class ProjectCreate(ProjectBase):
    """Class for new `Project` received on API."""

    pass
