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

    assert det.probability == 0.8 and det.label == 2

    assert obj.get_detection(10) == None


def test_calc_label(make_test_obj: Object):
    obj = make_test_obj

    assert round(obj.probability, 2) == 0.4
    assert obj.label == 1

    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.5, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.3, 2, 4))
    obj.add_detection(Detection(BBox(*[25, 35, 45, 55]), 0.8, 2, 4))

    assert round(obj.probability, 3) == 0.343
    assert obj.label == 2
