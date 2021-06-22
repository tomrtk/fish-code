"""Test api helper functions."""
import pytest

from core.api.api import (
    construct_pagination_data,
    convert_to_jobbare,
    convert_to_projectbare,
)
from core.api.schema import JobBare, ProjectBare
from core.model import Job, Project


def test_convert_to_projectbare():
    """Test converting from regular projec to projectbare."""
    valid_project = Project(
        name="Test Project",
        description="A small testproject.",
        number="4",
        location="Ether",
    )
    valid_project.id = 1

    # Assert single project.
    output_projectbare: ProjectBare = convert_to_projectbare(valid_project)
    assert type(output_projectbare) is ProjectBare

    # Assert invalid project. Use job as type.
    invalid_project = Job("Test job", "A test job", "Ether")

    with pytest.raises(TypeError):
        convert_to_projectbare(invalid_project)  # type: ignore

    # Assert basic type (int)
    with pytest.raises(TypeError):
        convert_to_projectbare(int)  # type: ignore


def test_convert_to_jobbare():
    """Test converting from regular projec to projectbare."""
    valid_job = Job(
        name="Test Project",
        description="A small testproject.",
        location="Ether",
    )
    valid_job.id = 1

    # Assert single project.
    output_jobbare: JobBare = convert_to_jobbare(valid_job)
    assert type(output_jobbare) is JobBare

    # Assert invalid job. Use project as type.
    invalid_job = Project(
        name="Test Project",
        description="A small testproject.",
        number="4",
        location="Ether",
    )

    with pytest.raises(TypeError):
        convert_to_jobbare(invalid_job)  # type: ignore

    # Assert basic type (int)
    with pytest.raises(TypeError):
        convert_to_jobbare(int)  # type: ignore


def test_construct_pagination_data():
    """Test construction of pagination data."""
    data = {
        "x-next-page": "1",
        "x-page": "1",
        "x-per-page": "10",
        "x-prev-page": "1",
        "x-total": "1",
        "x-total-pages": "1",
    }

    assert data == construct_pagination_data(1, 1, 10)
