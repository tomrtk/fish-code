"""Integration tests for schema."""

from datetime import datetime
from core import model
from core.api import schema

import pytest


def test_job_stats():
    """Test converting model.Job to schema.JobStats."""
    job = model.Job("name", "desc", "testland")

    job.add_object(
        model.Object(
            1,
            [
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 1),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 2),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 3),
            ],
        )
    )
    job.add_object(
        model.Object(
            2,
            [
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 1),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 2),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 3),
            ],
        )
    )
    job.add_object(
        model.Object(
            2,
            [
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 3),
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 4),
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 5),
            ],
        )
    )

    schema_stats = schema.JobStat(**job.stats)

    assert schema_stats.total_labels == 2
    assert schema_stats.total_objects == 3

    assert schema.get_label(1) in schema_stats.labels
    assert schema.get_label(2) in schema_stats.labels

    print(type(schema_stats.labels[schema.get_label(1)]))
    assert schema_stats.labels[schema.get_label(1)] == 1


def test_job_from_job():
    """Tried to convert a model.Job to schema.Job."""
    job = model.Job("name", "desc", "testland")

    job.add_object(
        model.Object(
            1,
            [
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 1),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 2),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 1, 3),
            ],
        )
    )
    job.add_object(
        model.Object(
            2,
            [
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 1),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 2),
                model.Detection(model.BBox(10, 10, 20, 30), 0.8, 2, 3),
            ],
        )
    )
    job.add_object(
        model.Object(
            2,
            [
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 3),
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 4),
                model.Detection(model.BBox(30, 10, 40, 20), 0.8, 2, 5),
            ],
        )
    )

    # Populate with "useless" data.
    job.id = 1
    for o in job._objects:
        o.time_in = datetime(2021, 1, 1, 10, 10, 10)
        o.time_out = datetime(2021, 1, 1, 10, 10, 12)
        o.id = 1

    sch_job = schema.Job.from_orm(job)
    assert sch_job.stats.total_objects == 3
    assert sch_job.stats.total_labels == 2
    assert sch_job.stats.labels[schema.get_label(1)] == 1
    assert sch_job.stats.labels[schema.get_label(2)] == 2
    assert sch_job.id == 1

    with pytest.raises(KeyError):
        sch_job.stats.labels["1"]
