"""Unit test of config package functionality."""
import configparser
import logging
import pytest
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

    assert set(parser.sections()) == set(
        ["GLOBAL", "CORE", "TRACING", "DETECTION", "UI"]
    )
    assert parser.get("DEFAULT", "hostname") == "127.0.0.1"
    assert parser.getboolean("DEFAULT", "enable") == True
    assert parser.getboolean("GLOBAL", "development") == False


def test_load_config_from_disk(preserve_config, cleanup_tmp_config, caplog):
    """Checks that config can be read from disk at default config location."""
    config.write_config(config.get_default_config())
    with caplog.at_level(logging.INFO):
        _ = config.load_config()
        assert caplog.records[0].getMessage() == "Configuration file found."


def test_config_not_found(preserve_config, caplog):
    """Checks that the config package does not find the config file if missing."""
    with caplog.at_level(logging.INFO):
        _ = config.load_config()
        assert (
            caplog.records[0].getMessage()
            == "Could not find config file, using defaults."
        )


def test_write_config(preserve_config, cleanup_tmp_config):
    """Test writing the config to file, then make sure its the same."""
    parser = configparser.ConfigParser()
    parser["TEST"] = {}
    parser["TEST"]["some_var"] = "Test, please ignore."
    config.write_config(parser)
    from_file = config.load_config()
    assert parser.__eq__(from_file)


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
