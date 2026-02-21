"""Integration tests for config commands."""

import pathlib

from click.testing import CliRunner

from requirements.main import cli

# =============================================================================
# config set tests
# =============================================================================


def test_config_set_color_enabled(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting color.enabled to true."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "set", "color.enabled", "true"])

    assert result.exit_code == 0
    assert "color.enabled enabled" in result.output


def test_config_set_color_disabled(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting color.enabled to false."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "set", "color.enabled", "false"])

    assert result.exit_code == 0
    assert "color.enabled disabled" in result.output


def test_config_set_pypi_index_url(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting pypi.index_url."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(
        cli,
        ["config", "set", "pypi.index_url", "https://nexus.example.com/simple/"],
    )

    assert result.exit_code == 0
    assert "pypi.index_url = https://nexus.example.com/simple/" in result.output


def test_config_set_pypi_fallback_url(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting pypi.fallback_url."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(
        cli, ["config", "set", "pypi.fallback_url", "https://pypi.org/simple/"]
    )

    assert result.exit_code == 0
    assert "pypi.fallback_url = https://pypi.org/simple/" in result.output


def test_config_set_invalid_url(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting pypi.index_url with invalid URL."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "set", "pypi.index_url", "not-a-url"])

    assert result.exit_code == 1
    assert "Invalid URL" in result.output
    assert "http://" in result.output or "https://" in result.output


def test_config_set_invalid_setting(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting an unknown setting."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "set", "invalid.setting", "value"])

    assert result.exit_code == 1
    assert "Unknown setting" in result.output


def test_config_set_invalid_bool_value(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test setting color.enabled with invalid boolean."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "set", "color.enabled", "maybe"])

    assert result.exit_code == 1
    assert "Invalid boolean" in result.output


# =============================================================================
# config unset tests
# =============================================================================


def test_config_unset_existing_setting(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test unsetting an existing setting."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    # First set a value
    cli_runner.invoke(
        cli,
        ["config", "set", "pypi.index_url", "https://nexus.example.com/simple/"],
    )

    # Then unset it
    result = cli_runner.invoke(cli, ["config", "unset", "pypi.index_url"])

    assert result.exit_code == 0
    assert "Removed pypi.index_url" in result.output


def test_config_unset_nonexistent_setting(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test unsetting a setting that doesn't exist."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "unset", "pypi.index_url"])

    assert result.exit_code == 0
    assert "was not set" in result.output


def test_config_unset_invalid_setting(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test unsetting an unknown setting."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    result = cli_runner.invoke(cli, ["config", "unset", "invalid.setting"])

    assert result.exit_code == 1
    assert "Unknown setting" in result.output


# =============================================================================
# config show tests
# =============================================================================


def test_config_show_displays_pypi_settings(
    cli_runner: CliRunner, fake_home: pathlib.Path, monkeypatch
) -> None:
    """Test that config show displays pypi settings."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: fake_home)

    # Set pypi settings
    cli_runner.invoke(
        cli,
        ["config", "set", "pypi.index_url", "https://nexus.example.com/simple/"],
    )
    cli_runner.invoke(
        cli, ["config", "set", "pypi.fallback_url", "https://pypi.org/simple/"]
    )

    result = cli_runner.invoke(cli, ["config", "show"])

    assert result.exit_code == 0
    assert "pypi.index_url" in result.output
    assert "pypi.fallback_url" in result.output
    assert "nexus.example.com" in result.output
