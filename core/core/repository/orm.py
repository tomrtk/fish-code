"""Mapping of tables in DB to objects in domain model."""
import logging

from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from core import model

logger = logging.getLogger(__name__)

# Constant values

NAME_SIZE: int = 60
DESCRIPTION_SIZE: int = 255

metadata = MetaData()

# Defining database tables

projects = Table(
    "projects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", Text(NAME_SIZE), nullable=False),
    Column("number", Text(NAME_SIZE), nullable=False, unique=True),
    Column("description", Text(DESCRIPTION_SIZE)),
)

jobs = Table(
    "jobs",
    metadata,
    Column("id", Integer, primary_key=True, nullable=False, unique=True),
    Column("name", Text(NAME_SIZE), nullable=False),
    Column("project_id", Integer, ForeignKey("projects.id")),
)


def start_mappers():
    """Map the relationships between tables defines above and domain model objects."""
    logger.info("Starting mappers")
    jobs_mapper = mapper(model.Job, jobs)

    projects_mapper = mapper(
        model.Project,
        projects,
        properties={
            "_jobs": relationship(
                jobs_mapper,
                collection_class=attribute_mapped_collection("id"),
                cascade="all, delete",
            )
        },
    )
