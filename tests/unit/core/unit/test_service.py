"""Unit tests for service functions in core."""
from typing import Any
from unittest.mock import patch

import pytest

from core import interface, services
from core.model import Object, Status
from core.services import (
    _bulk_job_status_change,
    get_directory_listing,
    get_job_objects,
    process_job,
)


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

    result = get_job_objects(1, 999, 0, 1)
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


def test_get_directory_listing():
    """Tests the accociated function that it generates the correct jsTree json."""
    response = get_directory_listing(
        "tests/integration/test_data/test_directory_listing_folder",
    )

    result = [
        {
            "id": "tests/integration/test_data/test_directory_listing_folder",
            "text": "test_directory_listing_folder",
            "type": "folder",
            "children": [
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/folderA",
                    "text": "folderA",
                    "type": "folder",
                    "children": True,
                },
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/folderB",
                    "text": "folderB",
                    "type": "folder",
                    "children": True,
                },
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/emptyfile",
                    "text": "emptyfile",
                    "type": "file",
                },
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/invalidext.in21p3",
                    "text": "invalidext.in21p3",
                    "type": "file",
                },
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/text.txt",
                    "text": "text.txt",
                    "type": "text/plain",
                },
                {
                    "id": "tests/integration/test_data/test_directory_listing_folder/video.mp4",
                    "text": "video.mp4",
                    "type": "video/mp4",
                },
            ],
        },
    ]

    assert response[0] is not None
    assert isinstance(response[0], dict)
    assert "children" in response[0]

    for p in response[0]["children"]:
        assert p in result[0]["children"]

    # Test normpath
    response = get_directory_listing(
        "tests//////integration/test_data//////test_directory_listing_folder//////",
    )
    assert response[0] is not None
    assert isinstance(response[0], dict)
    assert "children" in response[0]

    for p in response[0]["children"]:
        assert p in result[0]["children"]

    with pytest.raises(NotADirectoryError):
        get_directory_listing(
            "tests/integration/test_data/test_directory_listing_folder/emptyfile",
        )

    with pytest.raises(FileNotFoundError):
        get_directory_listing("this/path/should/not/exist")


@patch("os.access", return_value=False)
def test_get_directory_listing_permission_error(mock, tmp_path) -> None:
    """Test if directory is not accessible."""
    error_dir = tmp_path / "test"
    error_dir.mkdir()

    with pytest.raises(PermissionError):
        _ = get_directory_listing(str(error_dir))


def test_bulk_job_status_change(make_test_project_repo) -> None:
    """Test bulk change of status for jobs."""
    repo = make_test_project_repo

    _bulk_job_status_change(
        repo.session,
        [Status.RUNNING, Status.QUEUED],
        Status.PAUSED,
    )

    projects = repo.list()

    assert projects[0].jobs[0].status() is Status.DONE
    assert projects[0].jobs[1].status() is Status.PAUSED
    assert projects[0].jobs[2].status() is Status.PAUSED

    with pytest.raises(NotImplementedError):
        _bulk_job_status_change(
            repo.session,
            [Status.PAUSED],
            Status.DONE,
        )


@pytest.mark.parametrize(
    ("side_effect_raises", "expexted_status"),
    [
        (RuntimeError, Status.ERROR),
        (ConnectionError, Status.PAUSED),
        (KeyboardInterrupt, Status.PAUSED),
    ],
)
def test_process_job_errors(
    make_test_project_repo,
    side_effect_raises,
    expexted_status,
) -> None:
    """Test error handling in `process_job`."""
    import threading

    repo = make_test_project_repo
    event = threading.Event()
    event.set()

    assert repo.get(1).jobs[3].status() == Status.QUEUED

    with patch.object(services.Detector, "_models") as mock_1:
        mock_1.return_value = [
            interface.Model(
                "fishy",
                [
                    "test",
                ],
            ),
        ]
        with patch.object(services.Detector, "predict") as mock_2:

            def side_effect(*args: Any) -> None:
                raise side_effect_raises

            mock_2.side_effect = side_effect
            process_job(1, 4, event, repo.session)

        assert repo.get(1).jobs[3].status() == expexted_status
