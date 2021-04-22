"""Unit tests for conversions"""

import numpy as np
from PIL import Image

from core.interface import img_to_byte


def test_img_to_byte():
    original = np.array(Image.open("abbor.png"))

    byte = img_to_byte(original)
    back_to_img = np.array(Image.open(byte))

    np.testing.assert_allclose(original, back_to_img)
