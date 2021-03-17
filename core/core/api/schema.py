"""Pydantic shema of object recived and sent on API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from core import model


class HashableBaseModel(BaseModel):
    """Custom definition of `BaseModel` who implements `__hash__`."""

    def __hash__(self) -> int:
        """Hash member variables values."""
        return hash((type(self),) + tuple(self.__dict__.values()))


class JobBase(HashableBaseModel):
    """Base model for `Job` class used in API."""

    name: str
    description: str


class Object(BaseModel):
    """Base model for `Object` class used in API."""

    label: int
    probability: float
    track_id: int
    time_in: datetime
    time_out: datetime

    class Config:
        """Pydantic configuration options."""

        orm_mode = True


class Job(JobBase):
    """`Job` class used to send object on API."""

    id: int
    status: model.Status
    objects: List[Object] = []

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

    pass


class ProjectBase(HashableBaseModel):
    """Base model for `Project` class used in API."""

    name: str
    number: str
    description: str
    location: Optional[str] = None


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
