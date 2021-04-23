"""Test api helper functions."""
import pytest

from core.api.api import construct_pagination_data, convert_to_bare
from core.api.schema import ProjectBare
from core.model import Job, Project


def test_convert_to_bare():
    """Test converting from regular projec to projectbare."""
    valid_project = Project(
        name="Test Project",
        description="A small testproject.",
        number="4",
        location="Ether",
    )
    valid_project.id = 1

    # Assert single project.
    output_projectbare: ProjectBare = convert_to_bare(valid_project)
    assert type(output_projectbare) is ProjectBare

    # Assert invalid project. Use job as type.
    invalid_project = Job("Test job", "A test job", "Ether")

    with pytest.raises(TypeError):
        convert_to_bare(invalid_project)  # type: ignore

    # Assert basic type (int)
    with pytest.raises(TypeError):
        convert_to_bare(int)  # type: ignore


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
