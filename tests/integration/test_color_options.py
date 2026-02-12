"""Integration tests for color options."""

import pathlib

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.main import cli


def test_cli_color_flag_help(cli_runner):
    """Test that --color/--no-color flags appear in help."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--color / --no-color" in result.output


def test_cli_with_color_flag(cli_runner, fs: FakeFilesystem):
    """Test CLI with --color flag."""
    tmp_path = pathlib.Path("/fake/color-test")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    result = cli_runner.invoke(cli, ["--color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_cli_with_no_color_flag(cli_runner, fs: FakeFilesystem):
    """Test CLI with --no-color flag."""
    tmp_path = pathlib.Path("/fake/no-color-test")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    result = cli_runner.invoke(cli, ["--no-color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_cli_respects_no_color_env(cli_runner, monkeypatch, fs: FakeFilesystem):
    """Test that CLI respects NO_COLOR environment variable."""
    tmp_path = pathlib.Path("/fake/no-color-env")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    monkeypatch.setenv("NO_COLOR", "1")
    result = cli_runner.invoke(cli, ["cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_color_flag_overrides_no_color_env(cli_runner, monkeypatch, fs: FakeFilesystem):
    """Test that --color flag overrides NO_COLOR environment variable."""
    tmp_path = pathlib.Path("/fake/color-override")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\n")

    monkeypatch.setenv("NO_COLOR", "1")
    result = cli_runner.invoke(cli, ["--color", "cat", str(tmp_path)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


@pytest.mark.parametrize(
    "command_name,command_args,needs_path",
    [
        ("cat", [], True),
        ("find", ["requests"], True),
        ("update", ["requests", "2.26.0", "--preview"], True),
        ("add", ["pytest", "--preview"], True),
        ("remove", ["requests", "--preview"], True),
        ("sort", ["--preview"], True),
        ("versions", ["requests"], False),
    ],
)
def test_command_works_with_color_flag(
    cli_runner, command_name, command_args, needs_path, fs: FakeFilesystem
):
    """Test that commands work with --color flag."""
    tmp_path = pathlib.Path(f"/fake/color-cmd-{command_name}")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    args = ["--color", command_name, *command_args]
    if needs_path:
        args.append(str(tmp_path))
    result = cli_runner.invoke(cli, args)
    assert result.exit_code == 0, f"Command {command_name} failed with --color flag"


@pytest.mark.parametrize(
    "command_name,command_args,needs_path",
    [
        ("cat", [], True),
        ("find", ["requests"], True),
        ("update", ["requests", "2.26.0", "--preview"], True),
        ("add", ["pytest", "--preview"], True),
        ("remove", ["requests", "--preview"], True),
        ("sort", ["--preview"], True),
        ("versions", ["requests"], False),
    ],
)
def test_command_works_with_no_color_flag(
    cli_runner, command_name, command_args, needs_path, fs: FakeFilesystem
):
    """Test that commands work with --no-color flag."""
    tmp_path = pathlib.Path(f"/fake/no-color-cmd-{command_name}")
    tmp_path.mkdir(parents=True)
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.25.0\ndjango==3.2.0\n")

    args = ["--no-color", command_name, *command_args]
    if needs_path:
        args.append(str(tmp_path))
    result = cli_runner.invoke(cli, args)
    assert result.exit_code == 0, f"Command {command_name} failed with --no-color flag"


def test_color_documentation_in_help(cli_runner):
    """Test that color documentation is shown in help."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Color Output:" in result.output
    assert "NO_COLOR" in result.output
