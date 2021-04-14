"""Unit tests for `api/schema.py`"""
from datetime import datetime

from core import model
from core.api import schema


def test_object():
    """Create Object and check validators."""
    obj = schema.Object(
        label=0,
        probability=0.7,
        _detections=[
            model.Detection(model.BBox(10, 20, 30, 40), 0.7, 1, 1),
            model.Detection(model.BBox(10, 20, 30, 40), 0.8, 1, 2),
            model.Detection(model.BBox(10, 20, 30, 40), 0.3, 1, 3),
            model.Detection(model.BBox(10, 20, 30, 40), 0.1, 2, 4),
            model.Detection(model.BBox(10, 20, 30, 40), 0.3, 2, 5),
        ],
        track_id=1,
        time_in=datetime(2020, 3, 28, 10, 20, 30),
        time_out=datetime(2020, 3, 28, 10, 20, 40),
    )

    assert obj.label == "Gjedde"
    assert obj.probability == 0.7
    assert obj.detections == {
        schema.get_label(1): [0.7, 0.8, 0.3],
        schema.get_label(2): [0.1, 0.3],
    }
