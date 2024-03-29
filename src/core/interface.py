"""Interface module for communicating with other packages like `Tracing`."""
import logging
from dataclasses import dataclass

import numpy as np
import requests

import core.model
from core.utils import img_to_byte

logger = logging.getLogger(__name__)


def to_track(
    frames: list[core.model.Frame],
    host: str = "http://127.0.0.1",
    port: str = "8001",
) -> list[core.model.Object]:
    """Send frames to tracker.

    Parameter
    ---------
    frames: List[Frame]
        All frames for period to track for
    host: str
        IP or hostname for tracker API. Default is "localhost"
    port: str
        Port for API. Default is "8001"

    Return:
    ------
    Optional[List[Object]] :
        List of objects that have been tracked. None if none found.

    Raises
    ------
    RuntimeError
        If time_{in,out} is None

    """
    data = [frame.to_json() for frame in frames]

    response = requests.post(
        f"{host}:{port}/tracking/track",
        json=data,
    )

    if response.status_code == 200:
        objects = [core.model.Object.from_api(**obj) for obj in response.json()]
        for o in objects:
            times = sorted(det.frame for det in o._detections)

            time_in = frames[times[0]].timestamp
            if time_in is None:  # pragma: no cover
                raise RuntimeError("Expected type datetime, got None")
            o.time_in = time_in

            time_out = frames[times[-1]].timestamp
            if time_out is None:  # pragma: no cover
                raise RuntimeError("Expected type datetime, got None")
            o.time_out = time_out
        return objects

    return []


@dataclass
class Model:
    """Containing detection model information."""

    name: str
    classes: list[str]


class Detector:
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

    def __init__(
        self,
        host: str = "http://127.0.0.1",
        port: str = "8003",
    ) -> None:
        self.host: str = host
        self.port: str = port
        self.available_models: list[Model] = self._models()
        logger.debug("Interface detector constructed")

    def predict(
        self,
        frames: np.ndarray,
        model_name: str,
    ) -> list[core.model.Frame]:
        """Call `/predictions/{model_name}/` endpoint to do inference.

        Parameters
        ----------
        frames      :   np.ndarray
                        Numpy array of 3 or 4 dimensions with `shape`
                        `(height, width, channels) or
                        (frame, height, width, channels)`.
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
        ConnectionError
            If detection api is unreachable
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
            byte_frames = [("images", img_to_byte(frames))]
        else:
            byte_frames = [("images", img_to_byte(img)) for img in frames]

        try:
            response = requests.post(
                f"{self.host}:{self.port}/predictions/{model_name}/",
                files=byte_frames,
            )
        except requests.ConnectionError as e:
            raise ConnectionError("Connection error to Detection API") from e

        if response.status_code != 200:
            logger.error(
                "Response from detection API was not 200, but %s (%s)",
                response.status_code,
                response.json(),
            )
            raise RuntimeError(
                f"Unexpected HTTP status code from Detection API: "
                f"{response.status_code}",
            )

        result: list[core.model.Frame] = []
        for frame_no, detections in response.json().items():
            # No detections found in frame
            if len(detections) == 0:
                result.append(core.model.Frame(int(frame_no), []))
            else:
                result.append(
                    core.model.Frame(
                        int(frame_no),
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
                                frame=int(frame_no),
                            )
                            for detection in detections
                        ],
                    ),
                )

        return result

    def _models(self) -> list[Model]:
        """Call `/models/` endpoint to get available models.

        Returns
        -------
        List[core.interface.Model]
            List of available model names.
        """
        try:
            response = requests.get(f"{self.host}:{self.port}/models/")
        except requests.ConnectionError as e:
            raise ConnectionError("Connection error to Detection API") from e

        if response.status_code == 200:
            return [Model(key, value) for key, value in response.json().items()]

        logger.warning(
            "Response from detection API was not 200, but %s (%s)",
            response.status_code,
            response.json(),
        )

        return []
