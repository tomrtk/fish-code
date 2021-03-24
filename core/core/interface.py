"""Interface module for communicating with other packages like `Tracing`."""
import io
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import requests
from PIL import Image

import core.model

logger = logging.getLogger(__name__)


def to_track(
    frames: List[core.model.Frame], host: str = "127.0.0.1", port: str = "8001"
) -> Optional[List[core.model.Object]]:
    """Send frames to tracker.

    Parameter
    ---------
    frames: List[Frame]
        All frames for period to track for
    host: str
        IP or hostname for tracker API. Default is "localhost"
    port: str
        Port for API. Default is "8001"

    Return
    ------
    Optional[List[Object]] :
        List of objects that have been tracked. None if none found.
    """
    data = [frame.to_json() for frame in frames]

    response = requests.post(
        f"http://{host}:{port}/tracking/track",
        json=data,
    )

    if response.status_code == 200:
        objects = [core.model.Object.from_api(**obj) for obj in response.json()]
        for o in objects:

            times = sorted([det.frame for det in o._detections])

            time_in = frames[times[0]].timestamp
            if time_in == None:
                time_in = datetime(1, 1, 1)
            o.time_in = time_in

            time_out = frames[times[-1]].timestamp
            if time_out == None:
                time_out = datetime(1, 1, 1)
            o.time_out = time_out
        return objects

    return None


@dataclass
class Model:
    """Containing detection model information."""

    name: str
    classes: List[str]


class Detector:  # pragma: no cover
    """Interface class to detection API.

    Parameters
    ----------
    host    :   str
                IP-address for detection API.
    port    :   str
                Port number detection API is responding.

    Methods
    -------
    predict(frames: ndarray, model_name: str)
        Call detection API to do inference on `frames` with `model_name`.

    Examples
    --------
    >>> video = Video.from_path("test.mp4")
    >>> frames = video[0:50]
    >>> detection_interface = interface.Detector()
    >>> model_name = detection_interface.available_models[0].name
    >>> detections = detection_interface.predict(frames, model_name)
    >>> type(detections)
    <class 'list'>
    >>> type(detections[0])
    <class 'model.Frame'>


    Raises
    ------
    KeyError
        If `model_name` is not a recognised name by detection API.
    NotImplementedError
        If `frames` is of wrong dimensions. Should be 3 or 4 with shape:
        `(height, width, channels) or (frame, height, width, channels)`
    """

    def __init__(self, host: str = "127.0.0.1", port: str = "8003") -> None:
        self.host: str = host
        self.port: str = port
        self.available_models: List[Model] = self._models()
        logger.debug("Interface detector constructed")

    def predict(
        self, frames: np.ndarray, model_name: str
    ) -> List[core.model.Frame]:
        """Call `/predictions/{model_name}/` endpoint to do inference on `frames`.

        Parameters
        ----------
        frames      :   np.ndarray
                        Numpy array of 3 or 4 dimensions with `shape`
                        `(height, width, channels) or (frame, height, width, channels)`.
        model_name  :   str
                        Name of model to be used.

        Returns
        -------
        List[core.model.Frame]
            A list of frames objects with detections.

        Raises
        ------
        KeyError
            If `model_name` is not a recognised name by detection API.
        NotImplementedError
            If `frames` is of wrong dimensions. Should be 3 or 4 with shape:
            `(height, width, channels) or (frame, height, width, channels)`
        """
        if not any(model_name == m.name for m in self.available_models):
            logger.warning(
                "`model_name` is unknown, %s is not %s",
                model_name,
                self.available_models,
            )
            raise KeyError

        # frames not in correct shape
        if frames.ndim < 3 or frames.ndim > 4:
            logger.warning("frame dimension of array is not 3 or 4")
            raise NotImplementedError

        # if a single image
        if frames.ndim == 3:
            byte_io = io.BytesIO()
            Image.fromarray(frames).save(byte_io, "png")
            byte_io.seek(0)
            byte_frames = [("images", byte_io)]
        else:
            byte_frames = list()
            for i in range(frames.shape[0]):
                byte_io = io.BytesIO()
                Image.fromarray(frames[i, ...]).save(byte_io, "png")
                byte_io.seek(0)
                byte_frames.append(("images", byte_io))

        response = requests.post(
            f"http://{self.host}:{self.port}/predictions/{model_name}/",
            files=byte_frames,
        )

        if response.status_code == 200:
            result: List[core.model.Frame] = []
            for frame_no, detections in response.json().items():

                # No detections found in frame
                if len(detections) == 0:
                    result.append(core.model.Frame(frame_no, []))
                else:
                    result.append(
                        core.model.Frame(
                            frame_no,
                            [
                                core.model.Detection(
                                    core.model.BBox(
                                        x1=detection["x1"],
                                        y1=detection["y1"],
                                        x2=detection["x2"],
                                        y2=detection["y2"],
                                    ),
                                    probability=detection["confidence"],
                                    label=detection["label"],
                                    frame=frame_no,
                                )
                                for detection in detections
                            ],
                        )
                    )

            return result

        logger.error(
            "Response from detection API was not 200, but %s (%s)",
            response.status_code,
            response.json(),
        )

        return list()

    def _models(self) -> List[Model]:
        """Call `/models/` endpoint to get available models.

        Returns
        -------
        List[core.interface.Model]
            List of available model names.
        """
        response = requests.get(f"http://{self.host}:{self.port}/models/")

        if response.status_code == 200:
            return [Model(key, value) for key, value in response.json().items()]

        logger.warning(
            "Response from detection API was not 200, but %s (%s)",
            response.status_code,
            response.json(),
        )

        return list()
