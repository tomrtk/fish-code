import pytest

from core.model import BBox, Detection, Object


@pytest.fixture
def make_test_obj() -> Object:
    obj = Object(1)
    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 1))
    obj.add_detection(Detection(BBox(*[15, 25, 35, 45]), 0.8, 2, 2))
    obj.add_detection(Detection(BBox(*[20, 30, 40, 50]), 0.1, 1, 3))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.5, 1, 4))

    return obj


def test_add_object(make_test_obj: Object):
    obj = make_test_obj
    assert obj.number_of_detections() == 4

    obj.add_detection(Detection(BBox(*[10, 20, 30, 40]), 1.0, 1, 5))
    assert obj.number_of_detections() == 5


def test_get_object(make_test_obj: Object):
    obj = make_test_obj

    det = obj.get_detection(1)

    assert det.score == 0.8 and det.label == 2

    assert obj.get_detection(10) == None
