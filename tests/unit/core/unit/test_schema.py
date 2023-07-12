"""Unit tests for `api/schema.py`."""
from datetime import datetime

import pytest

from core import model
from core.api import schema


def test_object():
    """Create Object and check validators."""
    obj = schema.Object(
        id=1,
        label=0,
        probability=0.7,
        _detections=[
            model.Detection(model.BBox(10, 20, 30, 40), 0.7, 1, 1, 1, 1),
            model.Detection(model.BBox(10, 20, 30, 40), 0.8, 1, 2, 2, 1),
            model.Detection(model.BBox(10, 20, 30, 40), 0.3, 1, 3, 3, 1),
            model.Detection(model.BBox(10, 20, 30, 40), 0.1, 2, 4, 4, 1),
            model.Detection(model.BBox(10, 20, 30, 40), 0.3, 2, 5, 5, 1),
        ],
        video_ids=[1],
        time_in=datetime(2020, 3, 28, 10, 20, 30),
        time_out=datetime(2020, 3, 28, 10, 20, 40),
    )

    assert obj.label == "Gjedde"
    assert obj.probability == 0.7
    assert obj.detections == {
        schema.get_label(1): [0.7, 0.8, 0.3],
        schema.get_label(2): [0.1, 0.3],
    }
    assert obj.video_ids[0] == 1


def test_job_stats_happycase():
    """Testing JobStat Happy case."""
    jobstats = schema.JobStat(total_objects=1, total_labels=1, labels={1: 1})
    assert jobstats.total_labels == 1
    assert jobstats.total_objects == 1
    assert jobstats.labels == {schema.get_label(1): 1}

    jobstats = schema.JobStat(
        total_objects=1,
        total_labels=1,
        labels={"label": 1},
    )
    assert jobstats.total_labels == 1
    assert jobstats.total_objects == 1
    assert jobstats.labels == {"label": 1}

    jobstats = schema.JobStat(total_objects=1, total_labels=1, labels={"1": 1})
    assert jobstats.total_labels == 1
    assert jobstats.total_objects == 1
    assert jobstats.labels == {"1": 1}


def test_job_stats_not_happycase():
    """Checking badcases for JobStat."""
    with pytest.raises(TypeError):
        _ = schema.JobStat(
            total_objects=2,
            total_labels=2,
            labels={[1, 2]: 1, "label": 2},
        )
