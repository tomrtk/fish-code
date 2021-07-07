"""Utility functions for api."""
from core import model
from core.api import schema


def convert_to_projectbare(project: model.Project) -> schema.ProjectBare:
    """Convert `model.Project` to `schema.ProjectBare`.

    Parameters
    ----------
    data : model.Project
        The data to convert from.

    Returns
    -------
    schema.Project
        Converted data from model to schema object.

    Raises
    ------
    TypeError
        When neither valid type is passed.
    """
    if not isinstance(project, model.Project):
        raise TypeError(
            f"{type(project)} in not of type model.Project.",
        )

    return schema.ProjectBare(
        id=project.id,
        name=project.name,
        number=project.number,
        description=project.description,
        location=project.location,
        job_count=len(project.jobs),
    )


def convert_to_jobbare(job: model.Job) -> schema.JobBare:
    """Convert `model.Job` to `schema.JobBare`.

    Parameters
    ----------
    data : model.Job
        The data to convert from.

    Returns
    -------
    schema.Job
        Converted data from model to schema object.

    Raises
    ------
    TypeError
        When neither valid type is passed.
    """
    if not isinstance(job, model.Job):
        raise TypeError(
            f"{type(job)} in not of type model.Job.",
        )

    return schema.JobBare(
        id=job.id,
        status=job._status,
        name=job.name,
        description=job.description,
        location=job.location,
        object_count=len(job._objects),
        video_count=len(job.videos),
        progress=job.progress,
        stats=job.stats,
    )
