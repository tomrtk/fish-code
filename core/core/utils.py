"""Utility functions."""
import cv2 as cv
import numpy as np
import core.model as model


def outline_detection(img: np.ndarray, bbx: model.BBox) -> np.ndarray:
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
        (255, 0, 0),
        1,
    )

    new_img = cv.cvtColor(new_img, cv.COLOR_RGB2BGR)  # type: ignore
    retval, new_img = cv.imencode(".jpeg", new_img)  # type:ignore
    if retval is None:
        raise RuntimeError
    return new_img
