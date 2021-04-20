"""Test api helper functions."""
from typing import List, Union

import pytest

from core.api.api import convert_to_bare
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
