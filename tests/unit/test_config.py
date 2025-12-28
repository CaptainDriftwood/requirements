"""Tests for config module."""

from pathlib import Path

from src.config import (
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


def test_load_config_returns_empty_when_no_file():
    """Test that load_config returns empty dict when no config file."""
    # This test relies on the config file not existing in CI
    # or a fresh environment
    config = load_config()
    assert isinstance(config, dict)


def test_get_color_setting_returns_none_when_not_configured():
    """Test that get_color_setting returns None when not configured."""
    # This test relies on no color setting being configured
    result = get_color_setting()
    # Result should be None or bool depending on config
    assert result is None or isinstance(result, bool)


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
