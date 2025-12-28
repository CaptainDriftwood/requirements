"""Integration tests for color options."""

import pytest

from src.main import cli


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


def test_cli_respects_no_color_env(cli_runner, tmp_path, monkeypatch):
    """Test that CLI respects NO_COLOR environment variable."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    monkeypatch.setenv("NO_COLOR", "1")
    result = cli_runner.invoke(cli, ["cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_color_flag_overrides_no_color_env(cli_runner, tmp_path, monkeypatch):
    """Test that --color flag overrides NO_COLOR environment variable."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    monkeypatch.setenv("NO_COLOR", "1")
    result = cli_runner.invoke(cli, ["--color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


@pytest.mark.parametrize(
    "command_name,command_args",
    [
        ("cat", []),
        ("find", ["requests"]),
        ("update", ["requests", "2.26.0", "--preview"]),
        ("add", ["pytest", "--preview"]),
        ("remove", ["requests", "--preview"]),
        ("sort", ["--preview"]),
    ],
)
def test_command_works_with_color_flag(cli_runner, tmp_path, command_name, command_args):
    """Test that commands work with --color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    result = cli_runner.invoke(cli, ["--color", command_name, *command_args, str(tmp_path)])
    assert result.exit_code == 0, f"Command {command_name} failed with --color flag"


@pytest.mark.parametrize(
    "command_name,command_args",
    [
        ("cat", []),
        ("find", ["requests"]),
        ("update", ["requests", "2.26.0", "--preview"]),
        ("add", ["pytest", "--preview"]),
        ("remove", ["requests", "--preview"]),
        ("sort", ["--preview"]),
    ],
)
def test_command_works_with_no_color_flag(cli_runner, tmp_path, command_name, command_args):
    """Test that commands work with --no-color flag."""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    result = cli_runner.invoke(cli, ["--no-color", command_name, *command_args, str(tmp_path)])
    assert result.exit_code == 0, f"Command {command_name} failed with --no-color flag"


def test_color_documentation_in_help(cli_runner):
    """Test that color documentation is shown in help."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Color Output:" in result.output
    assert "NO_COLOR" in result.output
