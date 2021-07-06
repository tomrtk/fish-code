"""Unit tests for service functions in core."""
import pytest

from core.model import Object
from core.services import get_job_objects


def test_get_job_objects(make_test_project_repo):
    """Test `get_job_objects` pagination result."""
    _ = make_test_project_repo

    result = get_job_objects(1, 1, 0, 1)

    assert isinstance(result, dict)
    assert "data" in result
    assert len(result["data"]) == 1
    assert isinstance(result["data"][0], Object)
    assert "total_objects" in result
    assert result["total_objects"] == 1000


def test_get_job_objects_exception():
    """Testing exceptions in function."""
    with pytest.raises(RuntimeError):
        _ = get_job_objects(1, 1, 0, 1)


def test_get_job_objects_wrong_project_job(make_test_project_repo):
    """Test `get_job_objects` with wrong input."""
    _ = make_test_project_repo

    result = get_job_objects(2, 1, 0, 1)
    assert result is None

    result = get_job_objects(1, 2, 0, 1)
    assert result is None


def test_get_job_objects_wrong_start_length(make_test_project_repo):
    """Test `get_job_objects` with to large `start` and `length`."""
    _ = make_test_project_repo

    result = get_job_objects(1, 1, 0, 10)

    assert result is not None
    assert "total_objects" in result
    assert result["total_objects"] == 1000

    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) == 10

    result = get_job_objects(1, 1, 900, 200)
    assert result is not None
    assert "data" in result
    assert len(result["data"]) == 100
