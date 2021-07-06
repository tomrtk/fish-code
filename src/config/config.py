"""Module to handle configuration application configuration parameters."""
import configparser
import logging
from os.path import expanduser, isfile
from pathlib import Path

logger = logging.getLogger(__name__)
config_file = "config.ini"


def _find_config_directory() -> str:
    # TODO: Check if windows or linux, use enviroment variables
    return expanduser("~") + "/.config/nina/"


def _get_default_config() -> configparser.ConfigParser:
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


def load_config() -> configparser.ConfigParser:
    """Load configuration data from disk into ConfigParser object."""
    # TODO: Check default config file enviroment variable
    # if default:
    #     logger.info("Using default configuration paramaters.")
    #     return _get_default_config()

    config = configparser.ConfigParser()
    config_folder = _find_config_directory()
    config_path = config_folder + config_file

    if isfile(config_path):
        config.read(config_path)
    else:
        logger.warning(
            "Could not find config file, creating new one at '{}'".format(
                config_path
            )
        )
        config = _get_default_config()
        Path(config_folder).mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as configfile:
            config.write(configfile)
            logger.info("New configuration file created from default.")

    return config
