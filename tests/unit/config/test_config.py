"""Unit test of config package functionality."""
from os.path import isfile
from pathlib import Path
from unittest.mock import patch
import configparser
import logging
import os
import pytest
import sys

from config import find_config_directory
from config import find_data_directory
from config import load_config
from config import get_default_config
from config import write_config
from config import get_os_name
from config import get_video_root_path

logger = logging.getLogger(__name__)


def test_load_default_config() -> None:
    """Checks the default config to contain correct sections."""
    parser = load_config(default=True)

    assert set(parser.sections()) == {
        "GLOBAL",
        "CORE",
        "TRACING",
        "DETECTION",
        "UI",
    }
    assert parser.get("DEFAULT", "hostname") == "127.0.0.1"
    assert parser.getboolean("DEFAULT", "enable") is True
    assert parser.getboolean("GLOBAL", "development") is False


@patch("os.path.isfile")
def test_load_config(mock_isfile) -> None:
    """Checks that config can be read from disk at default config location."""
    mock_isfile.return_value = True
    with patch.object(configparser.ConfigParser, "read_file") as mock_method:
        load_config(path="./tests/integration/test_data/test_config.ini")

    mock_method.assert_called_once()


@patch("os.path.isfile")
def test_load_config_not_found(mock_isfile) -> None:
    """Checks that config can be read from disk at default config location."""
    mock_isfile.return_value = False
    with patch.object(configparser.ConfigParser, "read_file") as mock_method:
        data = load_config()

    mock_method.assert_not_called()
    assert data.__eq__(get_default_config())


@patch("os.path.isfile")
def test_load_config_oserror(mock_isfile, caplog) -> None:
    """Checks config error handling."""
    mock_isfile.return_value = True
    with patch.object(configparser.ConfigParser, "read_file") as mock_method:

        def side_effect(args):
            raise OSError

        mock_method.side_effect = side_effect
        with caplog.at_level(logging.ERROR):
            parser = load_config()
            assert (
                "Unable to read configuration file from"
                in caplog.records[0].getMessage()
            )
            assert parser.__eq__(get_default_config())


@patch("builtins.open")
def test_write_config(mock_open) -> None:
    """Checks that config can be written to disk at default config location."""
    with patch.object(configparser.ConfigParser, "write") as mock_method:
        write_config(get_default_config())

    mock_method.assert_called_once()
    mock_open.assert_called_once()


def test_read_config_garbage_data(caplog) -> None:
    """Test that malformed configuration files throws error, and gives default conf."""
    with caplog.at_level(logging.WARNING):
        parser = load_config(
            path="./tests/integration/test_data/malformed_config.ini"
        )
        assert (
            caplog.records[0].getMessage()
            == "Parsing error occured in config file."
        )
        assert parser.__eq__(get_default_config())

    with caplog.at_level(logging.WARNING):
        parser = load_config(
            path="./tests/integration/test_data/missing_header.ini"
        )
        assert (
            caplog.records[2].getMessage()
            == "Config file is missing section header."
        )
        assert parser.__eq__(get_default_config())


@pytest.mark.skipif(os.name == "nt", reason="Not run on Windows")
@pytest.mark.parametrize(
    "name, env, config_path, expected",
    [
        (
            "posix",
            "XDG_CONFIG_HOME",
            "/posix/test/path",
            "/posix/test/path/nina",
        ),
        ("DUMMY", "HOME", "/home/test/path", "/home/test/path/.config/nina"),
        ("DUMMY", "DUMMY", "DUMMY", str(Path().resolve())),
    ],
)
def test_find_config_dir(
    name: str, env: str, config_path: str, expected: str
) -> None:
    """Test finding application config directory based on os."""
    with patch("os.name", return_value=name), patch.dict(
        "os.environ", {env: config_path}, clear=True
    ):
        assert find_config_directory() == Path(expected)


@pytest.mark.skipif(not os.name == "nt", reason="Only run on Windows")
@pytest.mark.parametrize(
    "env, config_path, expected",
    [
        (
            "LOCALAPPDATA",
            "C:\\User\\test\\path",
            "C:\\User\\test\\path\\nina",
        ),
    ],
)
def test_find_config_dir_windows(
    env: str, config_path: str, expected: str
) -> None:
    """Test finding application config directory based on os."""
    with patch.dict("os.environ", {env: config_path}, clear=True):
        assert find_config_directory() == Path(expected)


@pytest.mark.skipif(os.name == "nt", reason="Not run on Windows")
@pytest.mark.parametrize(
    "name, env, config_path, expected",
    [
        ("posix", "XDG_DATA_HOME", "/posix/test/path", "/posix/test/path/nina"),
        (
            "DUMMY",
            "HOME",
            "/home/test/path",
            "/home/test/path/.local/share/nina",
        ),
        ("DUMMY", "DUMMY", "DUMMY", str(Path().resolve())),
    ],
)
def test_find_data_dir(
    name: str, env: str, config_path: str, expected: str
) -> None:
    """Test finding application data directory based on os."""
    with patch("os.name", name), patch.dict(
        "os.environ", {env: config_path}, clear=True
    ):
        assert find_data_directory() == Path(expected)


@pytest.mark.skipif(not os.name == "nt", reason="Only run on Windows")
@pytest.mark.parametrize(
    "env, config_path, expected",
    [
        (
            "LOCALAPPDATA",
            "C:\\User\\test\\path",
            "C:\\User\\test\\path\\nina",
        ),
    ],
)
def test_find_data_dir_windows(
    env: str, config_path: str, expected: str
) -> None:
    """Test finding application data directory based on os."""
    with patch.dict("os.environ", {env: config_path}, clear=True):
        assert find_data_directory() == Path(expected)


@pytest.mark.skipif(not os.name == "nt", reason="Only run on Windows")
def test_get_os_name_windows() -> None:
    """Test get os name."""
    assert get_os_name() == "nt"


@pytest.mark.skipif(not os.name == "posix", reason="Only run on posix")
def test_get_os_name_posix() -> None:
    """Test get os name."""
    assert get_os_name() == "posix"


@pytest.mark.skipif(not os.name == "nt", reason="Only run on Windows")
@pytest.mark.parametrize(
    "env, config_path, expected",
    [
        (
            "HOMEPATH",
            "C:\\User\\test\\path",
            "C:\\User\\test\\path",
        ),
    ],
)
def test_video_root_dir_windows(
    env: str, config_path: str, expected: str
) -> None:
    """Test finding application video root directory based on os."""
    with patch.dict("os.environ", {env: config_path}, clear=True):
        assert get_video_root_path() == expected


@pytest.mark.skipif(os.name == "nt", reason="Not run on Windows")
@pytest.mark.parametrize(
    "env, config_path, expected",
    [
        ("HOME", "/home/test", "/home/test"),
        ("DUMMY", "DUMMY", str(Path(sys.executable).anchor)),
    ],
)
def test_video_root_dir_others(
    env: str, config_path: str, expected: str
) -> None:
    """Test finding application video root directory based on os."""
    with patch.dict("os.environ", {env: config_path}, clear=True):
        assert get_video_root_path() == expected
