"""Pydantic shema of object recived and sent on API."""
from typing import Optional

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


class Job(JobBase):
    """`Job` class used to send object on API."""

    id: int
    status: model.Status

    class Config:
        """Pydantic configuration options."""

        orm_mode = True
        fields = {"status": "_status"}
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

    class Config:
        """Pydantic configuration options."""

        orm_mode = True


class ProjectCreate(ProjectBase):
    """Class for new `Project` received on API."""

    pass
