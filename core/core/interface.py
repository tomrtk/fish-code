"""Interface module for communicating with other packages like `Tracing`."""

from dataclasses import asdict
from typing import List, Optional

import requests

import core.model


def to_track(
    frames: List[core.model.Frame], host: str = "localhost", port: str = "8001"
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
    data = [asdict(frame) for frame in frames]
    response = requests.post(
        f"http://{host}:{port}/tracking/track",
        json=data,
    )

    if response.status_code == 200:
        return [core.model.Object.from_api(**obj) for obj in response.json()]

    return None
