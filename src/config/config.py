"""Module to handle configuration application configuration parameters."""
import configparser
import logging
import os
import sys
from os import name as os_name
from pathlib import Path
from typing import Final, Optional

logger = logging.getLogger(__name__)

CONFIG_FILE_NAME: Final[str] = "config.ini"
DATABASE_FILE_NAME: Final[str] = "data.db"
APP_DIRECTORY_NAME: Final[str] = "nina"


def get_os_name() -> str:
    """Get operation system name from `os.name`."""
    return os_name


def find_config_directory() -> Path:
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
    if (
        get_os_name() == "nt" and "LOCALAPPDATA" in os.environ
    ):  # pragma: no cover
        confighome = Path(os.environ["LOCALAPPDATA"])
    elif get_os_name() == "posix" and "XDG_CONFIG_HOME" in os.environ:
        confighome = Path(os.environ["XDG_CONFIG_HOME"])
    elif "HOME" in os.environ:
        confighome = Path(os.environ["HOME"]) / ".config"
    else:
        # Unable to find config directory, defaulting to current directory.
        return Path().resolve()

    return Path(confighome) / APP_DIRECTORY_NAME


def find_data_directory() -> Path:
    """Find application data directory."""
    if (
        get_os_name() == "nt" and "LOCALAPPDATA" in os.environ
    ):  # pragma: no cover
        confighome = Path(os.environ["LOCALAPPDATA"])
    elif get_os_name() == "posix" and "XDG_DATA_HOME" in os.environ:
        confighome = Path(os.environ["XDG_DATA_HOME"])
    elif "HOME" in os.environ:
        confighome = Path(os.environ["HOME"]) / ".local" / "share"
    else:
        # Unable to find data directory, defaulting to current directory.
        return Path().resolve()

    return Path(confighome) / APP_DIRECTORY_NAME


def get_config_file_path() -> str:
    """Get configuration file path.

    Returns
    -------
    str     :
        Path represented as a string to the configuration file.
    """
    return os.path.join(find_config_directory(), CONFIG_FILE_NAME)


def get_database_file_path() -> str:
    """Get file path to the database file.

    Returns
    -------
    str     :
        Path represented as a string to the database file.
    """
    return os.path.join(find_data_directory(), DATABASE_FILE_NAME)


def get_video_root_path() -> str:
    """Get the default path for the application file browser.

    Defaults to the users home directory. Based on the HOME variable,
    or HOMEPATH for windows users.

    Returns
    -------
    str     :
        Path represented as a string to the users home directory.
    """
    if get_os_name() == "nt" and "HOMEPATH" in os.environ:  # pragma: no cover
        return str(Path(os.environ["HOMEPATH"]))
    elif "HOME" in os.environ:
        return str(Path(os.environ["HOME"]))
    else:
        logger.debug(
            "Unable to determine video root directory, defaulting to filesystem root."
        )
        return str(Path(sys.executable).anchor)


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
    default_config["CORE"]["database_path"] = get_database_file_path()
    default_config["CORE"]["video_root_path"] = get_video_root_path()
    default_config["TRACING"] = {}
    default_config["TRACING"]["port"] = "8001"
    default_config["DETECTION"] = {}
    default_config["DETECTION"]["port"] = "8003"
    return default_config


def load_config(
    default: bool = False, path: Optional[str] = None
) -> configparser.ConfigParser:
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

    if not path:
        config_path = get_config_file_path()
    else:
        config_path = path

    config = configparser.ConfigParser()

    if os.path.isfile(config_path):
        try:
            logger.info("Configuration file found.")
            config.read_file(open(config_path))
        except configparser.MissingSectionHeaderError:
            logger.error("Config file is missing section header.")
        except configparser.ParsingError:
            logger.error("Parsing error occured in config file.")
        except OSError:
            logger.error(
                f"Unable to read configuration file from {config_path}"
            )
        else:
            return config

        logger.warning(
            "Falling back to default configuration, errors occured with config file."
        )
        return get_default_config()

    else:
        logger.warning(
            f"Could not find config file at {config_path}, using defaults."
            f"Saving it to {config_path}"
        )
        config = get_default_config()
        write_config(config, config_path)
        return config


def write_config(config: configparser.ConfigParser, path: str) -> None:
    """Write a ConfigParser object to disk at the applications config file path."""
    with open(path, "w") as configfile:
        config.write(configfile)
