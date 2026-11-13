from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path
from typing import Optional

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9001


def _config_path() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_home = Path(xdg_config_home).expanduser()
    elif sys.platform == "win32":
        config_home = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif sys.platform == "darwin":
        config_home = Path.home() / "Library/Application Support"
    else:
        config_home = Path.home() / ".config"

    config_path = config_home / "pumpkinpi" / "config.ini"
    if config_path.is_file():
        return config_path

    if sys.platform.startswith("linux"):
        legacy_path = Path.home() / ".local/etc/pumpkinpi_config.d"
        if legacy_path.is_dir():
            return legacy_path / "config.ini"
        if legacy_path.is_file():
            return legacy_path

    return config_path


def _read_config_defaults() -> tuple[str, int]:
    path = _config_path()
    parser = configparser.ConfigParser()
    try:
        with path.open(encoding="utf-8") as config_file:
            parser.read_file(config_file)
    except FileNotFoundError:
        return DEFAULT_HOST, DEFAULT_PORT
    except configparser.Error as error:
        raise ValueError(f"Invalid PumpkinPi config file '{path}': {error}") from error

    host = parser.get("network", "host", fallback=DEFAULT_HOST)
    try:
        port = parser.getint("network", "port", fallback=DEFAULT_PORT)
    except ValueError as error:
        raise ValueError(f"Invalid port in PumpkinPi config file '{path}': {error}") from error
    return host, port


def resolve_network_options(argv: list[str]) -> tuple[str, int]:
    host: Optional[str] = None
    port: Optional[int] = None
    index = 0

    while index < len(argv):
        argument = argv[index]
        if argument in ("-h", "--host", "-p", "--port"):
            if index + 1 >= len(argv):
                raise ValueError(f"{argument} requires a value.")
            value = argv[index + 1]
            index += 2
        elif argument.startswith("--host="):
            value = argument.partition("=")[2]
            index += 1
            argument = "--host"
        elif argument.startswith("--port="):
            value = argument.partition("=")[2]
            index += 1
            argument = "--port"
        else:
            index += 1
            continue

        if argument in ("-h", "--host"):
            host = value
        else:
            try:
                port = int(value)
            except ValueError as error:
                raise ValueError(f"{argument} must be an integer.") from error

    if host is None or port is None:
        config_host, config_port = _read_config_defaults()
        if host is None:
            host = config_host
        if port is None:
            port = config_port

    assert host is not None and port is not None
    return host, port
