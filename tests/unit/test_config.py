"""Tests for config module."""

import pathlib

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.config import (
    _format_toml_value,
    get_color_setting,
    get_config_dir,
    get_config_file,
    get_default_config_content,
    get_pypi_fallback_url,
    get_pypi_index_url,
    get_setting,
    load_config,
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
