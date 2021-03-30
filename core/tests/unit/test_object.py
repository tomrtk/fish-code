"""Unit tests for Object."""
from datetime import datetime
from typing import List

import pytest
from sqlalchemy.sql.sqltypes import Integer

from core.model import BBox, Detection, Object

pytestmark = pytest.mark.usefixtures("make_test_obj")


def test_add_object(make_test_obj: List[Object]):
    """Test add object."""
    obj = make_test_obj[0]
    assert obj.number_of_detections() == 4

    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 5))
    assert obj.number_of_detections() == 5


def test_get_object(make_test_obj: List[Object]):
    """Test get object."""
    obj = make_test_obj[0]

    det = obj.get_detection(1)

    assert det.probability == 0.8 and det.label == 2

    assert obj.get_detection(10) == None


def test_calc_label(make_test_obj: List[Object]):
    """Test calculating label label and probability."""
    obj = make_test_obj[0]

    assert round(obj.probability, 2) == 0.4
    assert obj.label == 1
    assert isinstance(obj.label, int)

    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.5, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.3, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.8, 2, 4))

    assert round(obj.probability, 3) == 0.343
    assert obj.label == 2


def test_get_result(make_test_obj: List[Object]):
    """Test get result."""
    obj = make_test_obj[0]

    assert obj.get_results() == {
        "track_id": 1,
        "label": 1,
        "probability": 0.4,
        "time_in": datetime(2020, 3, 28, 10, 20, 30),
        "time_out": datetime(2020, 3, 28, 10, 40, 30),
    }

    obj.track_id = None

    assert obj.get_results() == {
        "track_id": None,
        "label": 1,
        "probability": 0.4,
        "time_in": datetime(2020, 3, 28, 10, 20, 30),
        "time_out": datetime(2020, 3, 28, 10, 40, 30),
    }


def test_get_result_no_time(make_test_obj: List[Object]):
    """Test get result when timestamps are None."""
    obj = make_test_obj[0]
    obj.time_in = None
    obj.time_out = None

    assert obj.get_results() == {
        "track_id": 1,
        "label": 1,
        "probability": 0.4,
        "time_in": None,
        "time_out": None,
    }
