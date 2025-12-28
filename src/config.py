"""User configuration module for storing settings in home directory.

This module provides user-configurable settings stored in ~/.requirements/config.toml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Try to import tomllib (Python 3.11+), fall back to tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]


CONFIG_DIR_NAME = ".requirements"
CONFIG_FILE_NAME = "config.toml"


def get_config_dir() -> Path:
    """Get the configuration directory path.

    Returns:
        Path to ~/.requirements directory.
    """
    return Path.home() / CONFIG_DIR_NAME


def get_config_file() -> Path:
    """Get the configuration file path.

    Returns:
        Path to ~/.requirements/config.toml.
    """
    return get_config_dir() / CONFIG_FILE_NAME


def load_config() -> dict[str, Any]:
    """Load user configuration from config file.

    Returns:
        Dictionary with configuration settings.
        Returns empty dict if config file doesn't exist.
    """
    config_file = get_config_file()

    if not config_file.exists():
        return {}

    try:
        with config_file.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def get_color_setting() -> bool | None:
    """Get the color setting from user configuration.

    Returns:
        True if color is enabled, False if disabled, None if not configured.
    """
    config = load_config()
    color_config = config.get("color", {})

    if isinstance(color_config, dict):
        enabled = color_config.get("enabled")
        if isinstance(enabled, bool):
            return enabled

    return None


def ensure_config_dir() -> Path:
    """Ensure the configuration directory exists.

    Returns:
        Path to the configuration directory.
    """
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def save_color_setting(enabled: bool) -> None:
    """Save the color setting to user configuration.

    Preserves any other existing configuration settings when writing.

    Args:
        enabled: Whether color output should be enabled.
    """
    ensure_config_dir()
    config_file = get_config_file()

    # Load existing config or create new
    config = load_config()

    # Update color setting
    if "color" not in config:
        config["color"] = {}
    config["color"]["enabled"] = enabled

    # Write config file in TOML format, preserving all settings
    _write_config(config_file, config)


def _write_config(config_file: Path, config: dict[str, Any]) -> None:
    """Write configuration to TOML file.

    Args:
        config_file: Path to the configuration file.
        config: Configuration dictionary to write.
    """
    with config_file.open("w") as f:
        f.write("# Requirements CLI Configuration\n")
        f.write("# This file is auto-generated. You can edit it manually.\n\n")

        for section, values in config.items():
            if isinstance(values, dict):
                f.write(f"[{section}]\n")
                for key, value in values.items():
                    f.write(f"{key} = {_format_toml_value(value)}\n")
                f.write("\n")
            else:
                f.write(f"{section} = {_format_toml_value(values)}\n")


def _format_toml_value(value: Any) -> str:
    """Format a value for TOML output.

    Args:
        value: Value to format.

    Returns:
        TOML-formatted string representation.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        items = ", ".join(_format_toml_value(item) for item in value)
        return f"[{items}]"
    return str(value)


def get_default_config_content() -> str:
    """Get the default configuration file content.

    Returns:
        Default TOML configuration content.
    """
    return """# Requirements CLI Configuration
# Place this file at ~/.requirements/config.toml

[color]
# Enable or disable colored output
# Options: true, false
# Default: auto-detected based on terminal support
# enabled = true
"""
