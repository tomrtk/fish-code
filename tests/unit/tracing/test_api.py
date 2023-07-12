"""Test of Tracing API."""
from fastapi.testclient import TestClient

from tracing.api import tracking


def test_track():
    """Test track endpoint."""
    with TestClient(tracking) as client:
        response = client.post(
            "/tracking/track",
            json=[
                {
                    "idx": 0,
                    "detections": [
                        {
                            "bbox": {
                                "x1": 1.0,
                                "y1": 1.0,
                                "x2": 2.0,
                                "y2": 2.0,
                            },
                            "label": 1,
                            "probability": 1.0,
                            "frame": 0,
                        },
                    ],
                    "timestamp": None,
                },
                {
                    "idx": 1,
                    "detections": [
                        {
                            "bbox": {
                                "x1": 2.0,
                                "y1": 2.0,
                                "x2": 3.0,
                                "y2": 3.0,
                            },
                            "label": 1,
                            "probability": 1.0,
                            "frame": 1,
                        },
                    ],
                    "timestamp": None,
                },
                {
                    "idx": 3,
                    "detections": [
                        {
                            "bbox": {
                                "x1": 3.0,
                                "y1": 3.0,
                                "x2": 4.0,
                                "y2": 4.0,
                            },
                            "label": 1,
                            "probability": 1.0,
                            "frame": 2,
                        },
                    ],
                    "timestamp": None,
                },
            ],
        )

        assert response.status_code == 200
