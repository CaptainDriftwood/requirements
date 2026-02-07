"""Tests for config module."""

from pathlib import Path

import pytest

from requirements.config import (
    _format_toml_value,
    get_color_setting,
    get_config_dir,
    get_config_file,
    get_default_config_content,
    load_config,
    save_color_setting,
)


def test_get_config_dir():
    """Test that config dir is in home directory."""
    config_dir = get_config_dir()
    assert config_dir.name == ".requirements"
    assert config_dir.parent == Path.home()


def test_get_config_file():
    """Test that config file is in config dir."""
    config_file = get_config_file()
    assert config_file.name == "config.toml"
    assert config_file.parent == get_config_dir()


def test_load_config_returns_empty_when_no_file(tmp_path, monkeypatch):
    """Test that load_config returns empty dict when no config file."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    config = load_config()
    assert config == {}


def test_get_color_setting_returns_none_when_not_configured(tmp_path, monkeypatch):
    """Test that get_color_setting returns None when not configured."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_color_setting()
    assert result is None


def test_save_and_load_color_setting(tmp_path, monkeypatch):
    """Test saving and loading color setting."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    save_color_setting(True)

    config_file = tmp_path / ".requirements" / "config.toml"
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
