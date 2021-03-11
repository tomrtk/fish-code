"""Mapping of tables in DB to objects in domain model."""
import logging

from sqlalchemy import (
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
)
from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection, collection
from sqlalchemy.sql.sqltypes import PickleType

from core import model

logger = logging.getLogger(__name__)

# Constant values

NAME_SIZE: int = 60
DESCRIPTION_SIZE: int = 255
PATH_SIZE: int = 255

metadata = MetaData()

# Defining database tables

projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text(NAME_SIZE), nullable=False),
    Column("number", Text(NAME_SIZE)),
    Column("description", Text(DESCRIPTION_SIZE)),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text(NAME_SIZE), nullable=False),
    Column("_status", Enum(model.Status), nullable=False),
    Column("description", Text(DESCRIPTION_SIZE)),
    Column("project_id", Integer, ForeignKey("projects.id")),
)

object_job_assoc = Table(
    "object_job_assoc",
    metadata,
    Column("job_id", Integer, ForeignKey("jobs.id")),
    Column("obj_id", Integer, ForeignKey("objects.id")),
)

objects = Table(
    "objects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("label", Integer, nullable=False),
    Column("probability", Float, nullable=False),
)

detections = Table(
    "detections",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("score", Float, nullable=False),
    Column("label", Integer, nullable=False),
    Column("bbox", PickleType, nullable=False),
    Column("frame", Integer, nullable=False),
    Column("object_id", Integer, ForeignKey("objects.id")),
)

videos = Table(
    "videos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("_path", Text(PATH_SIZE), nullable=False),
    Column("frames", Integer, nullable=False),
)


def start_mappers():
    """Map the relationships between tables defines above and domain model objects."""
    logger.info("Starting mappers")

    detection_mapper = mapper(
        model.Detection,
        detections,
    )

    object_mapper = mapper(
        model.Object,
        objects,
        properties={
            "_detections": relationship(
                detection_mapper,
                collection_class=list,
                cascade="all, delete",
            )
        },
    )

    jobs_mapper = mapper(
        model.Job,
        jobs,
        properties={
            "_objects": relationship(
                object_mapper,
                secondary=object_job_assoc,
                cascade="all",
            )
        },
    )

    projects_mapper = mapper(
        model.Project,
        projects,
        properties={
            "_jobs": relationship(
                jobs_mapper,
                collection_class=set,
                cascade="all, delete",
            )
        },
    )

    videos_mapper = mapper(
        model.Video,
        videos,
    )
