"""User configuration module for storing settings in home directory.

This module provides user-configurable settings stored in ~/.requirements/config.toml,
with support for project-level configuration in pyproject.toml and pip.conf integration.

Configuration priority (highest to lowest):
1. CLI arguments
2. Environment variables (REQUIREMENTS_CLI_*, PIP_INDEX_URL)
3. Project config ([tool.requirements-cli] in pyproject.toml)
4. User config (~/.requirements/config.toml)
5. pip.conf settings
6. Default values
"""

from __future__ import annotations

import configparser
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

# Type alias for valid configuration values
ConfigValue = bool | str | int | float | list[Any]

CONFIG_DIR_NAME: Final[str] = ".requirements"
CONFIG_FILE_NAME: Final[str] = "config.toml"
DEFAULT_INDEX_URL: Final[str] = "https://pypi.org/simple/"

# Pre-compiled regex pattern for parsing pip extra-index-url
_PIP_EXTRA_URL_SPLIT_PATTERN: Final = re.compile(r"[\s\n]+")
_PIP_NEWLINE_SPLIT_PATTERN: Final = re.compile(r"[\n\r]+")

# Module-level configuration cache
_config_cache: dict[str, Any] = {
    "merged": None,
    "user": None,
    "pip": None,
    "project": None,
    "project_root": None,
}


def clear_config_cache() -> None:
    """Clear the configuration cache.

    Call this after modifying configuration files to ensure fresh reads.
    """
    _config_cache["merged"] = None
    _config_cache["user"] = None
    _config_cache["pip"] = None
    _config_cache["project"] = None
    _config_cache["project_root"] = None


@dataclass
class PyPIConfig:
    """Resolved PyPI configuration with source tracking.

    Attributes:
        index_url: Primary PyPI index URL.
        fallback_url: Fallback URL if primary fails (network errors only).
        extra_index_urls: Additional index URLs to try.
        source: Where the index_url was resolved from.
    """

    index_url: str = DEFAULT_INDEX_URL
    fallback_url: str | None = None
    extra_index_urls: list[str] = field(default_factory=list)
    source: str = "default"


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
    if _config_cache["user"] is not None:
        return _config_cache["user"]

    config_file = get_config_file()

    if not config_file.exists():
        _config_cache["user"] = {}
        return {}

    try:
        with config_file.open("rb") as f:
            config = tomllib.load(f)
            _config_cache["user"] = config
            return config
    except (OSError, tomllib.TOMLDecodeError):
        _config_cache["user"] = {}
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


def get_setting(section: str, key: str) -> ConfigValue | None:
    """Get a configuration setting by section and key.

    Args:
        section: The configuration section (e.g., 'color', 'pypi').
        key: The key within the section (e.g., 'enabled', 'index_url').

    Returns:
        The configuration value, or None if not configured.
    """
    config = load_config()
    section_config = config.get(section, {})

    if isinstance(section_config, dict):
        return section_config.get(key)

    return None


def save_setting(section: str, key: str, value: ConfigValue) -> None:
    """Save a configuration setting.

    Args:
        section: The configuration section (e.g., 'color', 'pypi').
        key: The key within the section (e.g., 'enabled', 'index_url').
        value: The value to save.
    """
    ensure_config_dir()
    config_file = get_config_file()
    config = load_config()

    if section not in config:
        config[section] = {}
    config[section][key] = value

    _write_config(config_file, config)
    clear_config_cache()


def unset_setting(section: str, key: str) -> bool:
    """Remove a configuration setting.

    Args:
        section: The configuration section (e.g., 'color', 'pypi').
        key: The key within the section (e.g., 'enabled', 'index_url').

    Returns:
        True if the setting was removed, False if it didn't exist.
    """
    config_file = get_config_file()
    config = load_config()

    section_config = config.get(section, {})
    if not isinstance(section_config, dict) or key not in section_config:
        return False

    del section_config[key]

    # Remove empty sections
    if not section_config:
        del config[section]

    _write_config(config_file, config)
    clear_config_cache()
    return True


def get_pypi_index_url() -> str | None:
    """Get the PyPI index URL from configuration.

    Returns:
        The configured index URL, or None if not configured.
    """
    value = get_setting("pypi", "index_url")
    return value if isinstance(value, str) else None


def get_pypi_fallback_url() -> str | None:
    """Get the PyPI fallback URL from configuration.

    Returns:
        The configured fallback URL, or None if not configured.
    """
    value = get_setting("pypi", "fallback_url")
    return value if isinstance(value, str) else None


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
    config = load_config()

    if "color" not in config:
        config["color"] = {}
    config["color"]["enabled"] = enabled

    _write_config(config_file, config)
    clear_config_cache()


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
    match value:
        case bool():
            return str(value).lower()
        case str():
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\t", "\\t")
            )
            return f'"{escaped}"'
        case int() | float():
            return str(value)
        case list():
            items = ", ".join(_format_toml_value(item) for item in value)
            return f"[{items}]"
        case _:
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

[pypi]
# Custom PyPI index URL for version queries
# Default: https://pypi.org/simple/
# index_url = "https://nexus.example.com/repository/pypi/simple/"

# Fallback URL if the primary index fails (network errors only, not 404s)
# fallback_url = "https://pypi.org/simple/"

# Additional index URLs to search (checked in order after primary)
# extra_index_urls = ["https://private.example.com/simple/"]
"""


# =============================================================================
# Phase 1: Project-level configuration support
# =============================================================================


def find_project_root(start: Path | None = None) -> Path | None:
    """Find the project root by walking up directories.

    Looks for (in order):
    1. pyproject.toml - Python project marker
    2. .git - Repository root

    Args:
        start: Starting directory (defaults to current working directory).

    Returns:
        Path to project root, or None if not found.
    """
    # Use cache only when using default (cwd)
    if start is None and _config_cache["project_root"] is not None:
        return _config_cache["project_root"]

    current = start or Path.cwd()

    # Resolve to absolute path
    current = current.resolve()

    # First pass: look for pyproject.toml
    for directory in [current, *current.parents]:
        if (directory / "pyproject.toml").exists():
            if start is None:
                _config_cache["project_root"] = directory
            return directory

    # Second pass: look for .git
    for directory in [current, *current.parents]:
        git_path = directory / ".git"
        if git_path.exists():
            if start is None:
                _config_cache["project_root"] = directory
            return directory

    if start is None:
        _config_cache["project_root"] = None
    return None


def load_project_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load project-level config from pyproject.toml [tool.requirements-cli].

    Args:
        project_root: Path to project root (auto-detected if None).

    Returns:
        Configuration dictionary from [tool.requirements-cli] section,
        or empty dict if not found.
    """
    # Use cache only when auto-detecting project root
    if project_root is None and _config_cache["project"] is not None:
        return _config_cache["project"]

    if project_root is None:
        project_root = find_project_root()

    if project_root is None:
        if _config_cache["project"] is None:
            _config_cache["project"] = {}
        return {}

    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        if _config_cache["project"] is None:
            _config_cache["project"] = {}
        return {}

    try:
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        config = data.get("tool", {}).get("requirements-cli", {})
        # Only cache when using auto-detected root
        if _config_cache["project"] is None:
            _config_cache["project"] = config
        return config
    except (OSError, tomllib.TOMLDecodeError):
        if _config_cache["project"] is None:
            _config_cache["project"] = {}
        return {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override dict into base dict.

    Args:
        base: Base dictionary.
        override: Dictionary with values to override.

    Returns:
        Merged dictionary (new dict, doesn't modify inputs).
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# =============================================================================
# Phase 2: Environment variable support
# =============================================================================


def _get_env_config() -> dict[str, Any]:
    """Get configuration from environment variables.

    Supports:
    - REQUIREMENTS_CLI_INDEX_URL: Override index URL
    - REQUIREMENTS_CLI_FALLBACK_URL: Override fallback URL
    - REQUIREMENTS_CLI_EXTRA_INDEX_URLS: Comma-separated extra URLs
    - REQUIREMENTS_CLI_COLOR: Override color setting (true/false)
    - PIP_INDEX_URL: Fallback for index URL (lower priority)
    - PIP_EXTRA_INDEX_URL: Fallback for extra URLs (space or newline separated)

    Returns:
        Configuration dictionary from environment variables.
    """
    config: dict[str, Any] = {}

    # PyPI settings
    pypi_config: dict[str, Any] = {}

    # REQUIREMENTS_CLI_* takes precedence over PIP_*
    if (index_url := os.environ.get("REQUIREMENTS_CLI_INDEX_URL")) or (
        index_url := os.environ.get("PIP_INDEX_URL")
    ):
        pypi_config["index_url"] = index_url

    if fallback_url := os.environ.get("REQUIREMENTS_CLI_FALLBACK_URL"):
        pypi_config["fallback_url"] = fallback_url

    # Extra index URLs - REQUIREMENTS_CLI uses comma separation
    if extra_urls := os.environ.get("REQUIREMENTS_CLI_EXTRA_INDEX_URLS"):
        pypi_config["extra_index_urls"] = [
            url.strip() for url in extra_urls.split(",") if url.strip()
        ]
    elif extra_urls := os.environ.get("PIP_EXTRA_INDEX_URL"):
        # PIP uses space or newline separation
        pypi_config["extra_index_urls"] = [
            url.strip()
            for url in _PIP_EXTRA_URL_SPLIT_PATTERN.split(extra_urls)
            if url.strip()
        ]

    if pypi_config:
        config["pypi"] = pypi_config

    # Color settings
    color_env = os.environ.get("REQUIREMENTS_CLI_COLOR", "").lower()
    if color_env in ("true", "1", "yes"):
        config["color"] = {"enabled": True}
    elif color_env in ("false", "0", "no"):
        config["color"] = {"enabled": False}

    return config


# =============================================================================
# Phase 4: pip.conf parsing
# =============================================================================


def _get_pip_config_paths() -> list[Path]:
    """Get pip configuration file paths in priority order (lowest to highest).

    Returns:
        List of potential pip.conf paths, ordered by priority.
    """
    paths: list[Path] = []

    # System-wide config (lowest priority)
    if os.name == "nt":
        # Windows
        program_data = os.environ.get("PROGRAMDATA", "C:\\ProgramData")
        paths.append(Path(program_data) / "pip" / "pip.ini")
    else:
        # Unix/Linux/macOS
        paths.append(Path("/etc/pip.conf"))
        # XDG config
        xdg_config_dirs = os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg")
        for config_dir in xdg_config_dirs.split(":"):
            paths.append(Path(config_dir) / "pip" / "pip.conf")

    # User config
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            paths.append(Path(appdata) / "pip" / "pip.ini")
    else:
        # macOS Application Support
        paths.append(
            Path.home() / "Library" / "Application Support" / "pip" / "pip.conf"
        )
        # XDG user config
        xdg_config_home = os.environ.get(
            "XDG_CONFIG_HOME", str(Path.home() / ".config")
        )
        paths.append(Path(xdg_config_home) / "pip" / "pip.conf")
        # Legacy user config
        paths.append(Path.home() / ".pip" / "pip.conf")

    # Virtualenv config (highest priority for pip.conf)
    if virtual_env := os.environ.get("VIRTUAL_ENV"):
        if os.name == "nt":
            paths.append(Path(virtual_env) / "pip.ini")
        else:
            paths.append(Path(virtual_env) / "pip.conf")

    return paths


def _parse_pip_config(config_path: Path) -> dict[str, Any]:
    """Parse a pip configuration file.

    Args:
        config_path: Path to pip.conf file.

    Returns:
        Configuration dictionary with pypi settings.
    """
    if not config_path.exists():
        return {}

    try:
        parser = configparser.ConfigParser()
        parser.read(config_path)

        pypi_config: dict[str, Any] = {}

        # Get [global] section settings
        if parser.has_section("global"):
            if parser.has_option("global", "index-url"):
                pypi_config["index_url"] = parser.get("global", "index-url")

            if parser.has_option("global", "extra-index-url"):
                extra_urls_raw = parser.get("global", "extra-index-url")
                # Handle multi-line values (each URL on new line with indentation)
                extra_urls = [
                    url.strip()
                    for url in _PIP_NEWLINE_SPLIT_PATTERN.split(extra_urls_raw)
                    if url.strip()
                ]
                pypi_config["extra_index_urls"] = extra_urls

        if pypi_config:
            return {"pypi": pypi_config}
        return {}
    except (OSError, configparser.Error):
        return {}


def load_pip_config() -> dict[str, Any]:
    """Load configuration from pip.conf files.

    Reads pip configuration files from standard locations and extracts
    index-url and extra-index-url settings.

    Returns:
        Configuration dictionary with pypi settings.
    """
    if _config_cache["pip"] is not None:
        return _config_cache["pip"]

    merged_config: dict[str, Any] = {}

    for config_path in _get_pip_config_paths():
        pip_config = _parse_pip_config(config_path)
        if pip_config:
            merged_config = _deep_merge(merged_config, pip_config)

    _config_cache["pip"] = merged_config
    return merged_config


# =============================================================================
# Unified configuration loading
# =============================================================================


def load_merged_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load configuration with full hierarchy.

    Priority (lowest to highest):
    1. pip.conf settings
    2. User config (~/.requirements/config.toml)
    3. Project config ([tool.requirements-cli] in pyproject.toml)
    4. Environment variables

    Args:
        project_root: Path to project root (auto-detected if None).

    Returns:
        Merged configuration dictionary.
    """
    # Use cache only when auto-detecting project root
    if project_root is None and _config_cache["merged"] is not None:
        return _config_cache["merged"]

    # Start with pip.conf (lowest priority)
    config = load_pip_config()

    # Merge user config
    user_config = load_config()
    config = _deep_merge(config, user_config)

    # Merge project config
    project_config = load_project_config(project_root)
    config = _deep_merge(config, project_config)

    # Merge environment variables (highest priority)
    env_config = _get_env_config()
    merged = _deep_merge(config, env_config)

    # Only cache when using auto-detected root
    if project_root is None:
        _config_cache["merged"] = merged

    return merged


def get_effective_pypi_config(
    cli_index_url: str | None = None,
    cli_fallback_url: str | None = None,
    project_root: Path | None = None,
) -> PyPIConfig:
    """Get the effective PyPI configuration with all sources merged.

    Priority (highest to lowest):
    1. CLI arguments
    2. Environment variables
    3. Project config (pyproject.toml)
    4. User config (~/.requirements/config.toml)
    5. pip.conf settings
    6. Default values

    Args:
        cli_index_url: Index URL from CLI argument.
        cli_fallback_url: Fallback URL from CLI argument.
        project_root: Path to project root (auto-detected if None).

    Returns:
        PyPIConfig with resolved settings and source tracking.
    """
    # CLI takes highest priority
    if cli_index_url:
        merged = load_merged_config(project_root)
        pypi_config = merged.get("pypi", {})
        return PyPIConfig(
            index_url=cli_index_url,
            fallback_url=cli_fallback_url or pypi_config.get("fallback_url"),
            extra_index_urls=pypi_config.get("extra_index_urls", []),
            source="cli",
        )

    # Load merged config
    merged = load_merged_config(project_root)
    pypi_config = merged.get("pypi", {})

    # Determine source
    source = "default"

    # Check each source in reverse priority order to determine actual source
    env_config = _get_env_config()
    if env_config.get("pypi", {}).get("index_url"):
        source = "environment"
    else:
        project_config = load_project_config(project_root)
        if project_config.get("pypi", {}).get("index_url"):
            source = "project"
        else:
            user_config = load_config()
            if user_config.get("pypi", {}).get("index_url"):
                source = "user"
            else:
                pip_config = load_pip_config()
                if pip_config.get("pypi", {}).get("index_url"):
                    source = "pip.conf"

    return PyPIConfig(
        index_url=pypi_config.get("index_url", DEFAULT_INDEX_URL),
        fallback_url=cli_fallback_url or pypi_config.get("fallback_url"),
        extra_index_urls=pypi_config.get("extra_index_urls", []),
        source=source,
    )
