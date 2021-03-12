"""Interface module for communicating with other packages like `Tracing`."""

from dataclasses import asdict
from typing import List, Optional

import requests

from core.model import Frame, Object


def to_track(
    frames: List[Frame], host: str = "localhost", port: str = "8001"
) -> Optional[List[Object]]:
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
        return [Object.from_api(**obj) for obj in response.json()]

    return None
