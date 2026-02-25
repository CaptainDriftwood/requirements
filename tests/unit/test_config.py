"""Tests for config module."""

import os
import pathlib

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.config import (
    DEFAULT_INDEX_URL,
    PyPIConfig,
    _config_cache,
    _deep_merge,
    _format_toml_value,
    _get_env_config,
    clear_config_cache,
    find_project_root,
    get_color_setting,
    get_config_dir,
    get_config_file,
    get_default_config_content,
    get_effective_pypi_config,
    get_pypi_fallback_url,
    get_pypi_index_url,
    get_setting,
    load_config,
    load_merged_config,
    load_pip_config,
    load_project_config,
    save_color_setting,
    save_setting,
    unset_setting,
)


def test_get_config_dir():
    """Test that config dir is in home directory."""
    config_dir = get_config_dir()
    assert config_dir.name == ".requirements"
    assert config_dir.parent == pathlib.Path.home()


def test_get_config_file():
    """Test that config file is in config dir."""
    config_file = get_config_file()
    assert config_file.name == "config.toml"
    assert config_file.parent == get_config_dir()


def test_load_config_returns_empty_when_no_file(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that load_config returns empty dict when no config file."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    config = load_config()
    assert config == {}


def test_load_config_returns_empty_on_invalid_toml(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that load_config returns empty dict on invalid TOML."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    config_file = fake_home / ".requirements" / "config.toml"
    fs.create_file(config_file, contents="invalid toml [[[")

    config = load_config()
    assert config == {}
    # Cache should also store empty dict
    assert _config_cache["user"] == {}


def test_get_setting_returns_none_for_non_dict_section(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test get_setting returns None when section value is not a dict."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    # Create config with section as non-dict value
    config_file = fake_home / ".requirements" / "config.toml"
    fs.create_file(config_file, contents='color = "not a dict"')

    result = get_setting("color", "enabled")
    assert result is None


def test_get_color_setting_returns_none_when_not_configured(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that get_color_setting returns None when not configured."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    result = get_color_setting()
    assert result is None


def test_save_and_load_color_setting(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test saving and loading color setting."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    save_color_setting(True)

    config_file = fake_home / ".requirements" / "config.toml"
    assert config_file.exists()

    config = load_config()
    assert config.get("color", {}).get("enabled") is True

    assert get_color_setting() is True

    save_color_setting(False)
    assert get_color_setting() is False


def test_get_default_config_content():
    """Test that default config content is valid."""
    content = get_default_config_content()
    assert "[color]" in content
    assert "enabled" in content


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ('hello "world"', '"hello \\"world\\""'),
        ("back\\slash", '"back\\\\slash"'),
        ("new\nline", '"new\\nline"'),
        ("tab\there", '"tab\\there"'),
    ],
)
def test_format_toml_value_escapes_special_characters(input_value, expected):
    """Test that special characters in strings are properly escaped."""
    assert _format_toml_value(input_value) == expected


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (True, "true"),
        (False, "false"),
        (42, "42"),
        (3.14, "3.14"),
        ("simple", '"simple"'),
        ([1, 2, 3], "[1, 2, 3]"),
    ],
)
def test_format_toml_value_types(input_value, expected):
    """Test TOML formatting for various types."""
    assert _format_toml_value(input_value) == expected


def test_get_setting_returns_none_when_not_configured(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that get_setting returns None when not configured."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    result = get_setting("pypi", "index_url")
    assert result is None


def test_save_and_get_setting(fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch):
    """Test saving and loading settings with generic functions."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    save_setting("pypi", "index_url", "https://example.com/simple/")
    result = get_setting("pypi", "index_url")
    assert result == "https://example.com/simple/"


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("color", "enabled", True),
        ("color", "enabled", False),
        ("pypi", "index_url", "https://nexus.example.com/simple/"),
        ("pypi", "fallback_url", "https://pypi.org/simple/"),
    ],
)
def test_save_setting_various_types(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch, section, key, value
):
    """Test saving various setting types."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    save_setting(section, key, value)
    assert get_setting(section, key) == value


def test_unset_setting_removes_key(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that unset_setting removes a key."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    save_setting("pypi", "index_url", "https://example.com/simple/")
    assert get_setting("pypi", "index_url") is not None

    result = unset_setting("pypi", "index_url")
    assert result is True
    assert get_setting("pypi", "index_url") is None


def test_unset_setting_removes_empty_section(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that unset_setting removes empty sections."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    save_setting("pypi", "index_url", "https://example.com/simple/")
    unset_setting("pypi", "index_url")

    config = load_config()
    assert "pypi" not in config


def test_unset_setting_returns_false_if_not_exists(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that unset_setting returns False if setting doesn't exist."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    result = unset_setting("nonexistent", "setting")
    assert result is False


def test_get_pypi_index_url(fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch):
    """Test get_pypi_index_url returns configured URL."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    assert get_pypi_index_url() is None

    save_setting("pypi", "index_url", "https://nexus.example.com/simple/")
    assert get_pypi_index_url() == "https://nexus.example.com/simple/"


def test_get_pypi_fallback_url(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test get_pypi_fallback_url returns configured URL."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    assert get_pypi_fallback_url() is None

    save_setting("pypi", "fallback_url", "https://pypi.org/simple/")
    assert get_pypi_fallback_url() == "https://pypi.org/simple/"


def test_get_pypi_url_returns_none_for_non_string(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that PyPI URL getters return None for non-string values."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    save_setting("pypi", "index_url", 123)
    assert get_pypi_index_url() is None


def test_default_config_includes_pypi_section():
    """Test that default config content includes pypi section."""
    content = get_default_config_content()
    assert "[pypi]" in content
    assert "index_url" in content
    assert "fallback_url" in content
    assert "extra_index_urls" in content


# =============================================================================
# Phase 1: Project root detection and project config tests
# =============================================================================


def test_find_project_root_with_pyproject_toml(fs: FakeFilesystem):
    """Test finding project root via pyproject.toml."""
    project_root = pathlib.Path("/project")
    fs.create_file(project_root / "pyproject.toml", contents="[project]\nname = 'test'")
    subdir = project_root / "src" / "module"
    fs.create_dir(subdir)

    result = find_project_root(subdir)
    assert result == project_root


def test_find_project_root_with_git_directory(fs: FakeFilesystem):
    """Test finding project root via .git directory."""
    project_root = pathlib.Path("/project")
    fs.create_dir(project_root / ".git")
    subdir = project_root / "src" / "module"
    fs.create_dir(subdir)

    result = find_project_root(subdir)
    assert result == project_root


def test_find_project_root_pyproject_takes_precedence(fs: FakeFilesystem):
    """Test that pyproject.toml takes precedence over .git."""
    git_root = pathlib.Path("/project")
    fs.create_dir(git_root / ".git")
    pyproject_root = git_root / "subproject"
    fs.create_file(pyproject_root / "pyproject.toml", contents="[project]")
    subdir = pyproject_root / "src"
    fs.create_dir(subdir)

    result = find_project_root(subdir)
    assert result == pyproject_root


def test_find_project_root_returns_none_when_not_found(fs: FakeFilesystem):
    """Test that find_project_root returns None when no markers found."""
    fs.create_dir("/some/random/directory")
    result = find_project_root(pathlib.Path("/some/random/directory"))
    assert result is None


def test_load_project_config_from_pyproject(fs: FakeFilesystem):
    """Test loading config from pyproject.toml [tool.requirements-cli] section."""
    project_root = pathlib.Path("/project")
    pyproject_content = """
[tool.requirements-cli]
color = true

[tool.requirements-cli.pypi]
index_url = "https://private.example.com/simple/"
fallback_url = "https://pypi.org/simple/"
extra_index_urls = ["https://extra.example.com/simple/"]
"""
    fs.create_file(project_root / "pyproject.toml", contents=pyproject_content)

    config = load_project_config(project_root)
    assert config.get("color") is True
    assert (
        config.get("pypi", {}).get("index_url") == "https://private.example.com/simple/"
    )
    assert config.get("pypi", {}).get("fallback_url") == "https://pypi.org/simple/"
    assert config.get("pypi", {}).get("extra_index_urls") == [
        "https://extra.example.com/simple/"
    ]


def test_load_project_config_returns_empty_when_no_section(fs: FakeFilesystem):
    """Test that load_project_config returns empty dict when section missing."""
    project_root = pathlib.Path("/project")
    fs.create_file(project_root / "pyproject.toml", contents="[project]\nname = 'test'")

    config = load_project_config(project_root)
    assert config == {}


def test_load_project_config_returns_empty_when_no_file():
    """Test that load_project_config returns empty dict when no pyproject.toml."""
    config = load_project_config(pathlib.Path("/nonexistent"))
    assert config == {}


# =============================================================================
# Phase 2: Environment variable tests
# =============================================================================


def test_env_config_requirements_cli_index_url(monkeypatch):
    """Test REQUIREMENTS_CLI_INDEX_URL environment variable."""
    monkeypatch.setenv("REQUIREMENTS_CLI_INDEX_URL", "https://env.example.com/simple/")
    config = _get_env_config()
    assert config.get("pypi", {}).get("index_url") == "https://env.example.com/simple/"


def test_env_config_pip_index_url_fallback(monkeypatch):
    """Test PIP_INDEX_URL is used when REQUIREMENTS_CLI_INDEX_URL not set."""
    monkeypatch.setenv("PIP_INDEX_URL", "https://pip.example.com/simple/")
    config = _get_env_config()
    assert config.get("pypi", {}).get("index_url") == "https://pip.example.com/simple/"


def test_env_config_requirements_cli_takes_precedence(monkeypatch):
    """Test REQUIREMENTS_CLI_INDEX_URL takes precedence over PIP_INDEX_URL."""
    monkeypatch.setenv("REQUIREMENTS_CLI_INDEX_URL", "https://cli.example.com/simple/")
    monkeypatch.setenv("PIP_INDEX_URL", "https://pip.example.com/simple/")
    config = _get_env_config()
    assert config.get("pypi", {}).get("index_url") == "https://cli.example.com/simple/"


def test_env_config_fallback_url(monkeypatch):
    """Test REQUIREMENTS_CLI_FALLBACK_URL environment variable."""
    monkeypatch.setenv("REQUIREMENTS_CLI_FALLBACK_URL", "https://fallback.example.com/")
    config = _get_env_config()
    assert config.get("pypi", {}).get("fallback_url") == "https://fallback.example.com/"


def test_env_config_extra_index_urls_comma_separated(monkeypatch):
    """Test REQUIREMENTS_CLI_EXTRA_INDEX_URLS with comma separation."""
    monkeypatch.setenv(
        "REQUIREMENTS_CLI_EXTRA_INDEX_URLS",
        "https://extra1.example.com/,https://extra2.example.com/",
    )
    config = _get_env_config()
    assert config.get("pypi", {}).get("extra_index_urls") == [
        "https://extra1.example.com/",
        "https://extra2.example.com/",
    ]


def test_env_config_pip_extra_index_url_space_separated(monkeypatch):
    """Test PIP_EXTRA_INDEX_URL with space separation."""
    monkeypatch.setenv(
        "PIP_EXTRA_INDEX_URL", "https://extra1.example.com/ https://extra2.example.com/"
    )
    config = _get_env_config()
    assert config.get("pypi", {}).get("extra_index_urls") == [
        "https://extra1.example.com/",
        "https://extra2.example.com/",
    ]


def test_env_config_color_enabled(monkeypatch):
    """Test REQUIREMENTS_CLI_COLOR=true."""
    monkeypatch.setenv("REQUIREMENTS_CLI_COLOR", "true")
    config = _get_env_config()
    assert config.get("color", {}).get("enabled") is True


def test_env_config_color_disabled(monkeypatch):
    """Test REQUIREMENTS_CLI_COLOR=false."""
    monkeypatch.setenv("REQUIREMENTS_CLI_COLOR", "false")
    config = _get_env_config()
    assert config.get("color", {}).get("enabled") is False


def test_env_config_returns_empty_when_no_vars():
    """Test _get_env_config returns empty dict when no relevant vars."""
    # Clear any existing env vars
    for var in [
        "REQUIREMENTS_CLI_INDEX_URL",
        "REQUIREMENTS_CLI_FALLBACK_URL",
        "REQUIREMENTS_CLI_EXTRA_INDEX_URLS",
        "REQUIREMENTS_CLI_COLOR",
        "PIP_INDEX_URL",
        "PIP_EXTRA_INDEX_URL",
    ]:
        os.environ.pop(var, None)

    config = _get_env_config()
    # May have empty pypi dict or no pypi key
    assert config.get("pypi", {}).get("index_url") is None


# =============================================================================
# Phase 4: pip.conf parsing tests
# =============================================================================


def test_load_pip_config_from_user_location(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test loading pip.conf from user config location."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    pip_conf = fake_home / ".pip" / "pip.conf"
    pip_conf_content = """
[global]
index-url = https://pip-user.example.com/simple/
extra-index-url =
    https://extra1.example.com/simple/
    https://extra2.example.com/simple/
"""
    fs.create_file(pip_conf, contents=pip_conf_content)

    config = load_pip_config()
    assert (
        config.get("pypi", {}).get("index_url")
        == "https://pip-user.example.com/simple/"
    )
    assert config.get("pypi", {}).get("extra_index_urls") == [
        "https://extra1.example.com/simple/",
        "https://extra2.example.com/simple/",
    ]


def test_load_pip_config_returns_empty_when_no_file(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test load_pip_config returns empty dict when no pip.conf exists."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    config = load_pip_config()
    assert config == {}


# =============================================================================
# Deep merge tests
# =============================================================================


def test_deep_merge_simple():
    """Test simple key merging."""
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested():
    """Test nested dict merging."""
    base = {"pypi": {"index_url": "https://base.com/", "timeout": 30}}
    override = {"pypi": {"index_url": "https://override.com/"}}
    result = _deep_merge(base, override)
    assert result == {"pypi": {"index_url": "https://override.com/", "timeout": 30}}


def test_deep_merge_does_not_modify_inputs():
    """Test that deep_merge doesn't modify input dicts."""
    base = {"a": {"b": 1}}
    override = {"a": {"c": 2}}
    _deep_merge(base, override)
    assert base == {"a": {"b": 1}}
    assert override == {"a": {"c": 2}}


# =============================================================================
# Unified config loading tests
# =============================================================================


def test_load_merged_config_hierarchy(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test config hierarchy: env > project > user > pip.conf."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    # Set up pip.conf (lowest priority)
    pip_conf = fake_home / ".pip" / "pip.conf"
    fs.create_file(
        pip_conf,
        contents="[global]\nindex-url = https://pip.example.com/",
    )

    # Set up user config
    user_config = fake_home / ".requirements" / "config.toml"
    fs.create_file(
        user_config,
        contents='[pypi]\nindex_url = "https://user.example.com/"',
    )

    # Set up project config
    project_root = pathlib.Path("/project")
    fs.create_file(
        project_root / "pyproject.toml",
        contents='[tool.requirements-cli.pypi]\nindex_url = "https://project.example.com/"',
    )

    # Set env var (highest priority)
    monkeypatch.setenv("REQUIREMENTS_CLI_INDEX_URL", "https://env.example.com/")

    config = load_merged_config(project_root)
    # Env var should win
    assert config.get("pypi", {}).get("index_url") == "https://env.example.com/"


def test_load_merged_config_user_overrides_pip(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test user config overrides pip.conf."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    pip_conf = fake_home / ".pip" / "pip.conf"
    fs.create_file(pip_conf, contents="[global]\nindex-url = https://pip.example.com/")

    user_config = fake_home / ".requirements" / "config.toml"
    fs.create_file(
        user_config,
        contents='[pypi]\nindex_url = "https://user.example.com/"',
    )

    config = load_merged_config()
    assert config.get("pypi", {}).get("index_url") == "https://user.example.com/"


# =============================================================================
# PyPIConfig and get_effective_pypi_config tests
# =============================================================================


def test_pypi_config_defaults():
    """Test PyPIConfig default values."""
    config = PyPIConfig()
    assert config.index_url == DEFAULT_INDEX_URL
    assert config.fallback_url is None
    assert config.extra_index_urls == []
    assert config.source == "default"


def test_get_effective_pypi_config_cli_override(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test CLI argument takes highest priority."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    # Set up user config
    user_config = fake_home / ".requirements" / "config.toml"
    fs.create_file(
        user_config,
        contents='[pypi]\nindex_url = "https://user.example.com/"',
    )

    config = get_effective_pypi_config(cli_index_url="https://cli.example.com/")
    assert config.index_url == "https://cli.example.com/"
    assert config.source == "cli"


def test_get_effective_pypi_config_from_user(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test config from user config file."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    user_config = fake_home / ".requirements" / "config.toml"
    fs.create_file(
        user_config,
        contents='[pypi]\nindex_url = "https://user.example.com/"',
    )

    config = get_effective_pypi_config()
    assert config.index_url == "https://user.example.com/"
    assert config.source == "user"


def test_get_effective_pypi_config_from_env(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test config from environment variable."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    monkeypatch.setenv("REQUIREMENTS_CLI_INDEX_URL", "https://env.example.com/")

    config = get_effective_pypi_config()
    assert config.index_url == "https://env.example.com/"
    assert config.source == "environment"


def test_get_effective_pypi_config_from_project(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test config from project pyproject.toml."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    project_root = pathlib.Path("/project")
    fs.create_file(
        project_root / "pyproject.toml",
        contents='[tool.requirements-cli.pypi]\nindex_url = "https://project.example.com/"',
    )

    config = get_effective_pypi_config(project_root=project_root)
    assert config.index_url == "https://project.example.com/"
    assert config.source == "project"


def test_get_effective_pypi_config_default():
    """Test default config when nothing is configured."""
    config = get_effective_pypi_config()
    assert config.index_url == DEFAULT_INDEX_URL
    assert config.source == "default"


def test_get_effective_pypi_config_with_extra_urls(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test extra_index_urls are included in config."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    user_config = fake_home / ".requirements" / "config.toml"
    fs.create_file(
        user_config,
        contents='[pypi]\nextra_index_urls = ["https://extra.example.com/"]',
    )

    config = get_effective_pypi_config()
    assert config.extra_index_urls == ["https://extra.example.com/"]


# =============================================================================
# Caching tests
# =============================================================================


def test_clear_config_cache_resets_all_keys():
    """Test that clear_config_cache resets all cache keys to None."""
    # Set some values in the cache
    _config_cache["user"] = {"some": "value"}
    _config_cache["pip"] = {"other": "value"}
    _config_cache["project"] = {"project": "config"}
    _config_cache["merged"] = {"merged": "config"}
    _config_cache["project_root"] = pathlib.Path("/some/path")

    clear_config_cache()

    assert _config_cache["user"] is None
    assert _config_cache["pip"] is None
    assert _config_cache["project"] is None
    assert _config_cache["merged"] is None
    assert _config_cache["project_root"] is None


def test_load_config_uses_cache(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that load_config returns cached value on second call."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    config_file = fake_home / ".requirements" / "config.toml"
    fs.create_file(config_file, contents="[color]\nenabled = true")

    # First call loads from file
    config1 = load_config()
    assert config1 == {"color": {"enabled": True}}
    assert _config_cache["user"] == {"color": {"enabled": True}}

    # Modify file (but cache should still return old value)
    config_file.write_text("[color]\nenabled = false")

    # Second call returns cached value
    config2 = load_config()
    assert config2 == {"color": {"enabled": True}}


def test_save_setting_clears_cache(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that save_setting clears the config cache."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    fs.create_dir(fake_home / ".requirements")

    # Load config to populate cache
    load_config()

    # Set a value in merged cache to verify it gets cleared
    _config_cache["merged"] = {"cached": "value"}

    save_setting("pypi", "index_url", "https://example.com/")

    # Cache should be cleared
    assert _config_cache["merged"] is None
    assert _config_cache["user"] is None


def test_save_color_setting_clears_cache(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that save_color_setting clears the config cache."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)
    fs.create_dir(fake_home / ".requirements")

    # Populate cache
    _config_cache["user"] = {"old": "value"}
    _config_cache["merged"] = {"cached": "value"}

    save_color_setting(True)

    # Cache should be cleared
    assert _config_cache["merged"] is None
    assert _config_cache["user"] is None


def test_unset_setting_clears_cache(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that unset_setting clears the config cache."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    config_file = fake_home / ".requirements" / "config.toml"
    fs.create_file(config_file, contents='[pypi]\nindex_url = "https://example.com/"')

    # Load and populate cache
    load_config()
    _config_cache["merged"] = {"cached": "value"}

    unset_setting("pypi", "index_url")

    # Cache should be cleared
    assert _config_cache["merged"] is None
    assert _config_cache["user"] is None


def test_load_merged_config_uses_cache(
    fs: FakeFilesystem, fake_home: pathlib.Path, monkeypatch
):
    """Test that load_merged_config returns cached value on second call."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    config_file = fake_home / ".requirements" / "config.toml"
    fs.create_file(config_file, contents="[color]\nenabled = true")

    # First call loads and caches
    config1 = load_merged_config()
    assert _config_cache["merged"] is not None

    # Modify file
    config_file.write_text("[color]\nenabled = false")

    # Second call returns cached value
    config2 = load_merged_config()
    assert config1 == config2


def test_find_project_root_uses_cache(fs: FakeFilesystem, monkeypatch):
    """Test that find_project_root caches result when using default start."""
    project = pathlib.Path("/test/project")
    fs.create_file(project / "pyproject.toml", contents="[project]")
    monkeypatch.chdir(project)

    # First call
    root1 = find_project_root()
    assert root1 == project
    assert _config_cache["project_root"] == project

    # Second call returns cached value
    root2 = find_project_root()
    assert root2 == project


def test_find_project_root_no_cache_with_explicit_start(
    fs: FakeFilesystem, monkeypatch
):
    """Test that find_project_root doesn't use cache with explicit start path."""
    project1 = pathlib.Path("/test/project1")
    project2 = pathlib.Path("/test/project2")
    fs.create_file(project1 / "pyproject.toml", contents="[project]")
    fs.create_file(project2 / "pyproject.toml", contents="[project]")
    monkeypatch.chdir(project1)

    # Call with explicit start - should not affect cache
    root = find_project_root(start=project2)
    assert root == project2

    # Cache should not be updated by explicit start call
    assert _config_cache["project_root"] is None
