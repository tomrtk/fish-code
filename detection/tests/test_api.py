"""Test of detection API."""
from fastapi.testclient import TestClient

from detection.api import detection_api


def test_list_models():
    """Test getting project list endpoint."""
    with TestClient(detection_api) as client:
        response = client.get("/models/")

        assert response.status_code == 200
        assert response.json() == ["fishy"]


def test_predict():
    """Test prediction of one image."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/fishy/",
            files=[
                ("images", open("./tests/test_data/mort3.png", "rb")),
            ],
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1

        # Testing if all keys are present
        assert "0" in data
        assert "x1" in data["0"][0]
        assert "y1" in data["0"][0]
        assert "x2" in data["0"][0]
        assert "y2" in data["0"][0]
        assert "confidence" in data["0"][0]
        assert "label" in data["0"][0]


def test_predict_no_results():
    """Test prediction of one image with no results."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/fishy/",
            files=[
                ("images", open("./tests/test_data/white.jpg", "rb")),
            ],
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0


def test_predict_wrong_model_name():
    """Test prediction for model_name not existing."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/test/",
            files=[
                ("images", open("./tests/test_data/white.jpg", "rb")),
            ],
        )

        assert response.status_code == 422


def test_predict_wrong_image_data_format():
    """Test prediction with wrong file type."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/test/",
            files=[
                ("images", open("./tests/test_data/test.txt", "rb")),
            ],
        )

        assert response.status_code == 422
