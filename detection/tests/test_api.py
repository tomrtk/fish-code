"""Test of detection API."""
import os
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from detection.api import detection_api, halve_batch

TEST_FILE_PATH = Path(os.path.dirname(__file__) + "/test_data/")


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


def test_halve_batch():
    """Test havling of batches."""
    batch = [[np.ones(5) for _ in range(10)]]
    batches = halve_batch(batch)

    assert len(batches) == 2
    assert len(batches[0]) == 5
    assert len(batches[1]) == 5

    batch = [[np.ones(5) for _ in range(11)]]

    batches = halve_batch(batch)

    assert len(batches) == 2
    assert len(batches[0]) == 5
    assert len(batches[1]) == 6
