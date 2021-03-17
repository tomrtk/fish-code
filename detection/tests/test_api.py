"""Test of detection API."""
from pathlib import Path

from fastapi.testclient import TestClient

from detection.api import detection_api

TEST_FILE_PATH = Path("./tests/test_data/")


def test_list_models():
    """Test getting project list endpoint."""
    with TestClient(detection_api) as client:
        response = client.get("/models/")

        assert response.status_code == 200
        result = response.json()
        assert "fishy" in result
        assert len(result["fishy"]) == 9


def test_predict():
    """Test prediction of one image."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/fishy/",
            files=[
                (
                    "images",
                    open(str((TEST_FILE_PATH / "mort3.png").resolve()), "rb"),
                ),
                (
                    "images",
                    open(str((TEST_FILE_PATH / "abbor.png").resolve()), "rb"),
                ),
            ],
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2

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
                (
                    "images",
                    open(str((TEST_FILE_PATH / "white.jpg").resolve()), "rb"),
                ),
            ],
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert len(data["0"]) == 0


def test_predict_wrong_model_name():
    """Test prediction for model_name not existing."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/test/",
            files=[
                (
                    "images",
                    open(str((TEST_FILE_PATH / "white.jpg").resolve()), "rb"),
                ),
            ],
        )

        assert response.status_code == 422


def test_predict_wrong_image_data_format():
    """Test prediction with wrong file type."""
    with TestClient(detection_api) as client:
        response = client.post(
            "/predictions/test/",
            files=[
                (
                    "images",
                    open(str((TEST_FILE_PATH / "test.txt").resolve()), "rb"),
                ),
            ],
        )

        assert response.status_code == 422
