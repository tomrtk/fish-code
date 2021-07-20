"""Utility functions."""
import io

import cv2 as cv
import numpy as np

import core.model as model

from typing import Tuple


def outline_detection(
    img: np.ndarray, bbx: model.BBox, color: Tuple[int, int, int]
) -> np.ndarray:
    """Convert numpy array to image and outline detection.

    Parameters
    ----------
    img     : np.ndarray
            Imagedata as numpy.ndarray
    bbx    : model.BBox
            Boundingbox associated with the detection

    Returns
    -------
    np.ndarray
            image encoded as jpeg
    """
    new_img = cv.rectangle(  # type: ignore
        img,
        (int(bbx.x1), int(bbx.y1)),
        (int(bbx.x2), int(bbx.y2)),
        color,
        1,
    )

    new_img = cv.cvtColor(new_img, cv.COLOR_RGB2BGR)  # type: ignore
    retval, new_img = cv.imencode(".jpeg", new_img)  # type:ignore
    if retval is None:
        raise RuntimeError
    return new_img


def img_to_byte(img: np.ndarray) -> io.BytesIO:
    """Convert image as np.ndarray to image byte.

    This tried to do as few check to keep it as fast as possible.

    Parameters
    ----------
    img : np.ndarray
        imagedata

    Return
    ------
    io.BytesIO
        Image data as byte.
    """
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # type: ignore
    retval, img_byte = cv.imencode(".png", img)  # type: ignore
    if not retval:
        raise RuntimeError("Unexpected error when converting image to byte.")
    return io.BytesIO(img_byte)
