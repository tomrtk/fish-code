from datetime import datetime

import pytest
from sqlalchemy.sql.sqltypes import Integer

from core.model import BBox, Detection, Object


@pytest.fixture
def make_test_obj() -> Object:
    obj = Object(1)
    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1))
    obj.add_detection(Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 2))
    obj.add_detection(Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 3))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 4))
    obj.track_id = 1

    return obj


def test_add_object(make_test_obj: Object):
    obj = make_test_obj
    assert obj.number_of_detections() == 4

    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 5))
    assert obj.number_of_detections() == 5


def test_get_object(make_test_obj: Object):
    obj = make_test_obj

    det = obj.get_detection(1)

    assert det.probability == 0.8 and det.label == 2

    assert obj.get_detection(10) == None


def test_calc_label(make_test_obj: Object):
    obj = make_test_obj

    assert round(obj.probability, 2) == 0.4
    assert obj.label == 1
    assert isinstance(obj.label, int)

    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.5, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.3, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.8, 2, 4))

    assert round(obj.probability, 3) == 0.343
    assert obj.label == 2


def test_get_result(make_test_obj: Object):
    obj = make_test_obj

    assert obj.get_results() == {
        "track_id": 1,
        "label": 1,
        "probability": 0.4,
        "time_in": datetime(1, 1, 1, 0, 0),
        "time_out": datetime(1, 1, 1, 0, 0),
    }

    obj.track_id = None

    assert obj.get_results() == {
        "track_id": None,
        "label": 1,
        "probability": 0.4,
        "time_in": datetime(1, 1, 1, 0, 0),
        "time_out": datetime(1, 1, 1, 0, 0),
    }
