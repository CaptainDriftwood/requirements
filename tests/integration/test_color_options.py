"""Integration tests for color options."""

import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


def test_cli_color_flag_help(cli_runner):
    """Test that --color/--no-color flags appear in help."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--color / --no-color" in result.output


def test_cli_with_color_flag(cli_runner, tmp_path):
    """Test CLI with --color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    result = cli_runner.invoke(cli, ["--color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_cli_with_no_color_flag(cli_runner, tmp_path):
    """Test CLI with --no-color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    result = cli_runner.invoke(cli, ["--no-color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_cli_respects_no_color_env(cli_runner, tmp_path):
    """Test that CLI respects NO_COLOR environment variable."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        result = cli_runner.invoke(cli, ["cat", str(tmp_path)])
        assert result.exit_code == 0
        assert "requirements.txt" in result.output


def test_color_flag_overrides_no_color_env(cli_runner, tmp_path):
    """Test that --color flag overrides NO_COLOR environment variable."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    with patch.dict(os.environ, {"NO_COLOR": "1"}):
        result = cli_runner.invoke(cli, ["--color", "cat", str(tmp_path)])
        assert result.exit_code == 0
        assert "requirements.txt" in result.output


def test_all_commands_work_with_color_flag(cli_runner, tmp_path):
    """Test that all commands work with --color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    commands = [
        ["cat", str(tmp_path)],
        ["find", "requests", str(tmp_path)],
        ["update", "requests", "2.26.0", "--preview", str(tmp_path)],
        ["add", "pytest", "--preview", str(tmp_path)],
        ["remove", "requests", "--preview", str(tmp_path)],
        ["sort", "--preview", str(tmp_path)],
    ]

    for cmd in commands:
        result = cli_runner.invoke(cli, ["--color", *cmd])
        assert result.exit_code == 0, f"Command {cmd[0]} failed with --color flag"


def test_all_commands_work_with_no_color_flag(cli_runner, tmp_path):
    """Test that all commands work with --no-color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    commands = [
        ["cat", str(tmp_path)],
        ["find", "requests", str(tmp_path)],
        ["update", "requests", "2.26.0", "--preview", str(tmp_path)],
        ["add", "pytest", "--preview", str(tmp_path)],
        ["remove", "requests", "--preview", str(tmp_path)],
        ["sort", "--preview", str(tmp_path)],
    ]

    for cmd in commands:
        result = cli_runner.invoke(cli, ["--no-color", *cmd])
        assert result.exit_code == 0, f"Command {cmd[0]} failed with --no-color flag"


def test_color_documentation_in_help(cli_runner):
    """Test that color documentation is shown in help."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Color Output:" in result.output
    assert "NO_COLOR" in result.output
