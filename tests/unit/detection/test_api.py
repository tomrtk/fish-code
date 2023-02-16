"""Test of detection API."""
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from detection.api import detection_api, halve_batch

TEST_FILE_PATH = Path(__file__).parent / "test_data"


@pytest.fixture(scope="module")
def client():
    with TestClient(detection_api) as client:
        yield client


def test_list_models(client):
    """Test getting project list endpoint."""
    response = client.get("/models/")

    assert response.status_code == 200
    result = response.json()
    assert "fishy" in result
    assert len(result["fishy"]) == 9


def test_predict(client):
    """Test prediction of one image."""
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


def test_predict_no_results(client):
    """Test prediction of one image with no results."""
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


def test_predict_wrong_model_name(client):
    """Test prediction for model_name not existing."""
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


def test_predict_wrong_image_data_format(client):
    """Test prediction with wrong file type."""
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
