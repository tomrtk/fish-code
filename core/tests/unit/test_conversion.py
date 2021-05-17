"""Unit tests for conversions."""

import cv2 as cv
import numpy as np
from PIL import Image

from core.model import BBox
from core.utils import img_to_byte, outline_detection


def test_img_to_byte():
    """Test image to byte conversion."""
    original = np.array(Image.open("./tests/unit/abbor.png"))

    byte = img_to_byte(original)
    back_to_img = np.array(Image.open(byte))

    np.testing.assert_allclose(original, back_to_img)


def test_outline_detection():
    img = np.zeros((10, 10, 3), dtype=np.float32)

    bbox = BBox(2, 2, 4, 4)

    jpeg = outline_detection(img, bbox)

    conv = cv.imdecode(jpeg, cv.IMREAD_COLOR)  # type: ignore

    assert conv.shape == (10, 10, 3)

    # checking corners are red-ish,
    # jpeg compression messes up the data
    assert conv[2, 4, 2] > 125
    assert conv[4, 2, 2] > 125
    assert conv[4, 4, 2] > 125
    assert conv[2, 2, 2] > 125

    assert conv[2, 4, :2].all() < 50
    assert conv[4, 2, :2].all() < 50
    assert conv[4, 4, :2].all() < 50
    assert conv[2, 2, :2].all() < 50
