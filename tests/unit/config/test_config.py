"""Unit test of config package functionality."""
import configparser
import logging
import pytest
from unittest.mock import patch
import os

import config
from os.path import isfile

logger = logging.getLogger(__name__)


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
    with patch.object(configparser.ConfigParser, "read_file") as mock_method:
        config.load_config()

    mock_method.assert_called_once()


@patch("os.path.isfile")
def test_load_config_not_found(mock_isfile):
    """Checks that config can be read from disk at default config location."""
    mock_isfile.return_value = False
    with patch.object(configparser.ConfigParser, "read_file") as mock_method:
        data = config.load_config()

    mock_method.assert_not_called()
    assert data.__eq__(config.get_default_config())


@patch("builtins.open")
def test_write_config(mock_open):
    """Checks that config can be written to disk at default config location."""
    with patch.object(configparser.ConfigParser, "write") as mock_method:
        config.write_config(config.get_default_config())

    mock_method.assert_called_once()
    mock_open.assert_called_once()


def test_read_config_garbage_data(caplog):
    """Test that malformed configuration files throws error, and gives default conf."""
    with caplog.at_level(logging.WARNING):
        parser = config.load_config(
            path="./tests/integration/test_data/malformed_config.ini"
        )
        assert (
            caplog.records[0].getMessage()
            == "Parsing error occured in config file."
        )
        assert parser.__eq__(config.get_default_config())

    with caplog.at_level(logging.WARNING):
        parser = config.load_config(
            path="./tests/integration/test_data/missing_header.ini"
        )
        assert (
            caplog.records[2].getMessage()
            == "Config file is missing section header."
        )
        assert parser.__eq__(config.get_default_config())
