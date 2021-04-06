"""Unit tests for Object."""
from datetime import datetime
from typing import List

import pytest

from core.model import BBox, Detection, Object


@pytest.mark.usefixtures("make_test_obj")
def test_add_object(make_test_obj: List[Object]):
    """Test add object."""
    obj = make_test_obj[0]
    assert obj.number_of_detections() == 4

    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 5))
    assert obj.number_of_detections() == 5


@pytest.mark.usefixtures("make_test_obj")
def test_get_object(make_test_obj: List[Object]):
    """Test get object."""
    obj = make_test_obj[0]

    det = obj.get_detection(1)

    assert det.probability == 0.8 and det.label == 2

    assert obj.get_detection(10) == None


@pytest.mark.usefixtures("make_test_obj")
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


@pytest.mark.usefixtures("make_test_obj")
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


@pytest.mark.usefixtures("make_test_obj")
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


def test_object_from_api():
    """Test creating an object from JSON expected from the API."""
    json = [
        {
            "track_id": 1,
            "detections": [
                {
                    "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                    "label": 7,
                    "probability": 0.9,
                    "frame": 900,
                }
            ],
            "label": 7,
        }
    ]
    objects = [Object.from_api(**obj) for obj in json]

    assert len(objects) == 1
    assert isinstance(objects, List)
    assert isinstance(objects[0], Object)
    obj = objects[0]
    assert obj.track_id == 1

    assert isinstance(obj._detections, List)
    assert len(obj._detections) == 1
    assert isinstance(obj._detections[0], Detection)
    det = obj._detections[0]
    assert det.bbox == BBox(10, 20, 30, 40)
    assert det.label == 7
    assert det.probability == 0.9
    assert det.frame == 900

    assert obj.label == 7


def test_object_from_api_multiple():
    """Test creating objects with multiple detections."""
    json = [
        {
            "track_id": 1,
            "detections": [
                {
                    "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                    "label": 3,
                    "probability": 0.8,
                    "frame": 900,
                },
                {
                    "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                    "label": 9,
                    "probability": 0.75,
                    "frame": 901,
                },
                {
                    "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                    "label": 3,
                    "probability": 0.4,
                    "frame": 902,
                },
            ],
            "label": 999,
        },
        {
            "track_id": 2,
            "detections": [
                {
                    "bbox": {"x1": 10, "y1": 20, "x2": 30, "y2": 40},
                    "label": 7,
                    "probability": 0.9,
                    "frame": 900,
                }
            ],
            "label": 7,
        },
    ]
    objects = [Object.from_api(**obj) for obj in json]

    assert len(objects) == 2
    obj1 = objects[0]
    obj2 = objects[1]

    assert len(obj1._detections) == 3
    assert len(obj2._detections) == 1

    assert obj1.label == 3
    assert obj2.label == 7

    assert obj1.probability == pytest.approx(0.4)
    assert obj2.probability == pytest.approx(0.9)
