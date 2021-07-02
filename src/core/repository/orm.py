"""Mapping of tables in DB to objects in domain model."""
import logging

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
)
from sqlalchemy.orm import registry, relationship
from sqlalchemy.sql.schema import ForeignKeyConstraint
from sqlalchemy.sql.sqltypes import PickleType

from core import model

mapper_registry = registry()

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
    Column("location", Text(DESCRIPTION_SIZE), nullable=True),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text(NAME_SIZE), nullable=False),
    Column("_status", Enum(model.Status), nullable=False),
    Column("description", Text(DESCRIPTION_SIZE)),
    Column("location", Text(DESCRIPTION_SIZE)),
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("next_batch", Integer, nullable=False),
    Column("progress", Integer, nullable=False),
)

object_job_assoc = Table(
    "object_job_assoc",
    metadata,
    Column("job_id", Integer, ForeignKey("jobs.id")),
    Column("obj_id", Integer, ForeignKey("objects.id")),
)

video_job_assoc = Table(
    "video_job_assoc",
    metadata,
    Column("job_id", Integer, ForeignKey("jobs.id")),
    Column("video_id", Integer, ForeignKey("videos.id")),
)

objects = Table(
    "objects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("label", Integer, nullable=False),
    Column("probability", Float, nullable=False),
    Column("track_id", Integer, nullable=True),
    Column("time_in", DateTime, nullable=True),
    Column("time_out", DateTime, nullable=True),
)

detections = Table(
    "detections",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("probability", Float, nullable=False),
    Column("label", Integer, nullable=False),
    Column("bbox", PickleType, nullable=False),
    Column("frame", Integer, nullable=False),
    Column("object_id", Integer, ForeignKey("objects.id")),
    Column("video_id", Integer, nullable=False),
    Column("frame_id", Integer, nullable=False),
    ForeignKeyConstraint(
        ["video_id", "frame_id"], ["frames.video_id", "frames.idx"]
    ),
)

frames = Table(
    "frames",
    metadata,
    Column("video_id", Integer, ForeignKey("videos.id"), primary_key=True),
    Column("idx", Integer, primary_key=True),
    Column("timestamp", DateTime, nullable=True),
)

videos = Table(
    "videos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("_path", Text(PATH_SIZE), nullable=False),
    Column("frame_count", Integer, nullable=False),
    Column("fps", Integer, nullable=False),
    Column("width", Integer, nullable=False),
    Column("height", Integer, nullable=False),
    Column("timestamp", DateTime),
    Column("output_width", Integer, nullable=False),
    Column("output_height", Integer, nullable=False),
)


def start_mappers() -> None:
    """Map the relationships.

    Map the relationships between tables defines above and domain model
    objects.
    """
    logger.info("Starting mappers")

    detection_mapper = mapper_registry.map_imperatively(
        model.Detection,
        detections,
    )

    frame_mapper = mapper_registry.map_imperatively(
        model.Frame,
        frames,
        properties={
            "detections": relationship(detection_mapper, cascade="all")
        },
    )

    object_mapper = mapper_registry.map_imperatively(
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

    videos_mapper = mapper_registry.map_imperatively(
        model.Video,
        videos,
        properties={
            "frames": relationship(frame_mapper, cascade="all, delete")
        },
    )

    jobs_mapper = mapper_registry.map_imperatively(
        model.Job,
        jobs,
        properties={
            "_objects": relationship(
                object_mapper,
                secondary=object_job_assoc,
                cascade="all",
            ),
            "videos": relationship(
                videos_mapper,
                secondary=video_job_assoc,
                cascade="all",
            ),
        },
    )

    mapper_registry.map_imperatively(
        model.Project,
        projects,
        properties={
            "jobs": relationship(
                jobs_mapper,
                collection_class=list,
                cascade="all, delete",
            )
        },
    )
