"""Module to handle configuration application configuration parameters."""
import configparser
import logging
from os.path import expanduser, isfile
from pathlib import Path

logger = logging.getLogger(__name__)
config_file = "config.ini"


def find_config_directory() -> str:
    """Get configuration directory.

    Returns
    -------
    str     :
        Path represented as a string to a directory.
        Ends with a trailing /
    """
    # TODO: Check if windows or linux, use enviroment variables
    return expanduser("~") + "/.config/nina/"


def get_default_config() -> configparser.ConfigParser:
    """Get default settings stored in ConfigParser object.

    Returns
    -------
    ConfigParser    :
        ConfigParser object containing default values.
    """
    default_config = configparser.ConfigParser()
    default_config["DEFAULT"]["hostname"] = "127.0.0.1"
    default_config["DEFAULT"]["enable"] = "true"
    default_config["GLOBAL"] = {}
    default_config["GLOBAL"]["development"] = "false"
    default_config["UI"] = {}
    default_config["UI"]["port"] = "5000"
    default_config["CORE"] = {}
    default_config["CORE"]["port"] = "8000"
    default_config["TRACING"] = {}
    default_config["TRACING"]["port"] = "8001"
    default_config["DETECTION"] = {}
    default_config["DETECTION"]["port"] = "8003"
    return default_config


def load_config(default: bool = False) -> configparser.ConfigParser:
    """Load configuration data from disk into ConfigParser object.

    Parameter
    ---------
    default :   bool
        True in order to get the default config, and ignore config file.
        This parameter is optional, and is defalt set to False.

    Returns
    -------
    ConfigParser    :
        ConfigParser object containing configuration options from disk.
        If the file does not exist, default configuration is returned instead.
    """
    if default:
        return get_default_config()

    config = configparser.ConfigParser()
    config_path = find_config_directory() + config_file

    if isfile(config_path):
        config.read(config_path)  # TODO: Should surround with try
        logger.info("Configuration file found.")
    else:
        logger.warning("Could not find config file, using defaults.")
        config = get_default_config()

    return config


def write_config(config: configparser.ConfigParser) -> None:
    """Write a ConfigParser object to disk at the applications config file path."""
    config_folder = find_config_directory()

    # TODO: Error check
    Path(config_folder).mkdir(parents=True, exist_ok=True)
    with open(config_folder + config_file, "w") as configfile:
        config.write(configfile)
        logger.info("New configuration file created from default.")
