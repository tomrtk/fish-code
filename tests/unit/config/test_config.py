"""Unit test of config package functionality."""
import configparser
import logging
import pytest
from unittest.mock import patch
import os

import config
from os.path import isfile

logger = logging.getLogger(__name__)


@pytest.fixture
def preserve_config(scope="module"):
    """Preserves the existing config file before running a function."""
    config_folder = config.find_config_directory()
    config_path = config.get_config_file_path()

    # Only backup config file if it is present
    if isfile(config_path):
        logger.info("Backing up config file...")
        os.rename(config_path, os.path.join(config_folder, "config.bak"))
        yield
        logger.info("Restoring config file...")
        os.rename(os.path.join(config_folder, "config.bak"), config_path)
    else:
        yield


@pytest.fixture
def cleanup_tmp_config(preserve_config, scope="function"):
    """Purges temporary config file from disk after each test."""
    config_path = config.get_config_file_path()
    yield
    if isfile(config_path):
        os.remove(config_path)


def test_load_default_config():
    """Checks the default config to contain correct sections."""
    parser = config.load_config(default=True)

    assert set(parser.sections()) == {
        "GLOBAL",
        "CORE",
        "TRACING",
        "DETECTION",
        "UI",
    }
    assert parser.get("DEFAULT", "hostname") == "127.0.0.1"
    assert parser.getboolean("DEFAULT", "enable") == True
    assert parser.getboolean("GLOBAL", "development") == False


@patch("os.path.isfile")
def test_load_config(mock_isfile):
    """Checks that config can be read from disk at default config location."""
    mock_isfile.return_value = True
    with patch.object(configparser.ConfigParser, "read") as mock_method:
        config.load_config()

    mock_method.assert_called_once()


@patch("os.path.isfile")
def test_load_config_not_found(mock_isfile):
    """Checks that config can be read from disk at default config location."""
    mock_isfile.return_value = False
    with patch.object(configparser.ConfigParser, "read") as mock_method:
        data = config.load_config()

    mock_method.assert_not_called()
    assert data.__eq__(config.get_default_config())


def test_write_config():
    """Checks that config can be read from disk at default config location."""
    with patch.object(configparser.ConfigParser, "write") as mock_method:
        mock_method.call
        config.write_config(config.get_default_config())

    mock_method.assert_called_once()
    assert mock_method.call_args[0][0].name == config.get_config_file_path()


def test_read_config_garbage_data(preserve_config, cleanup_tmp_config, caplog):
    """Test that malformed configuration files throws error, and gives default conf."""
    config_path = config.get_config_file_path()
    with open(config_path, "w") as configfile:
        text = [
            "[Just some garbage data]\n",
            "This is not a config file!\n",
            "= 2\n",
        ]
        configfile.writelines(text)

    with caplog.at_level(logging.ERROR):
        parser = config.load_config()
        assert (
            caplog.records[0].getMessage()
            == "Parsing error occured in config file."
        )
        assert parser.__eq__(config.get_default_config())

    with open(config_path, "w") as configfile:
        text = [
            "Just some garbage data",
        ]
        configfile.writelines(text)

    with caplog.at_level(logging.ERROR):
        parser = config.load_config()
        assert (
            caplog.records[1].getMessage()
            == "Config file is missing section header."
        )
        assert parser.__eq__(config.get_default_config())
