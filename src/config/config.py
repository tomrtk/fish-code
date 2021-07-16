"""Module to handle configuration application configuration parameters."""
import configparser
import logging
import os
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

CONFIG_FILE_NAME: Final[str] = "config.ini"
CONFIG_DIRECTORY_NAME: Final[str] = "nina"


def find_config_directory() -> Path:  # Pragma: no cover
    """Get configuration directory.

    Checks the operating system if it is windows or unix based. Uses enviroment
    variables 'LOCALAPPDATA', 'XDG_CONFIG_HOME', and 'HOME' to determine
    applications config directory. Defaults to the current working directory
    if none of the above enviroment variables are set.

    Returns
    -------
    Path    :
        Path object to the configuration directory.
    """
    if os.name == "nt" and "LOCALAPPDATA" in os.environ:
        confighome = Path(os.environ["LOCALAPPDATA"])
    elif os.name == "posix" and "XDG_CONFIG_HOME" in os.environ:
        confighome = Path(os.environ["XDG_CONFIG_HOME"])
    elif "HOME" in os.environ:
        confighome = Path(os.path.join(os.environ["HOME"], ".config"))
    else:
        # Unable to find config directory, defaulting to current directory.
        return Path().resolve()

    return Path(os.path.join(confighome, CONFIG_DIRECTORY_NAME))


def get_config_file_path() -> str:
    """Get configuration file path.

    Returns
    -------
    str     :
        Path represented as a string to the configuration file.
    """
    return os.path.join(find_config_directory(), CONFIG_FILE_NAME)


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
    default_config["CORE"]["batch_size"] = "100"
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
    config_path = get_config_file_path()

    if os.path.isfile(config_path):
        try:
            logger.info("Configuration file found.")
            config.read(config_path)
        except configparser.MissingSectionHeaderError:
            logger.error("Config file is missing section header.")
        except configparser.ParsingError:
            logger.error("Parsing error occured in config file.")
        else:
            return config

        logger.warning(
            "Falling back to default configuration, config file contains errors."
        )
        return get_default_config()

    else:
        logger.warning("Could not find config file, using defaults.")
        return get_default_config()


def write_config(config: configparser.ConfigParser) -> None:
    """Write a ConfigParser object to disk at the applications config file path."""
    # TODO: Error check
    Path(find_config_directory()).mkdir(parents=True, exist_ok=True)
    with open(get_config_file_path(), "w") as configfile:
        config.write(configfile)
