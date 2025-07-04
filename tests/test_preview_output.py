from pathlib import Path

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def runner():
    """Click test runner with stderr separation."""
    return CliRunner(mix_stderr=False)


def create_requirements_file(base_path: Path, subdir: str, content: str):
    """Create a requirements.txt file with given content."""
    project_dir = base_path / subdir
    project_dir.mkdir(exist_ok=True)

    file_path = project_dir / "requirements.txt"
    file_path.write_text(content)

    return file_path


def test_update_preview_output_format(runner, tmp_path):
    """Test that update command uses consistent output format in preview mode."""
    create_requirements_file(tmp_path, "project", "django==3.0\nrequests==2.25.1\n")

    result = runner.invoke(
        cli, ["update", "requests", "2.30.0", "--preview", str(tmp_path)]
    )

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show content with trailing newline
    assert "requests==2.30.0" in result.stdout


def test_add_preview_output_format(runner, tmp_path):
    """Test that add command uses consistent output format in preview mode."""
    create_requirements_file(tmp_path, "project", "django==3.0\n")

    result = runner.invoke(cli, ["add", "pytest", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show content with trailing newline
    assert "pytest" in result.stdout


def test_remove_preview_output_format(runner, tmp_path):
    """Test that remove command uses consistent output format in preview mode."""
    create_requirements_file(tmp_path, "project", "django==3.0\nrequests==2.25.1\n")

    result = runner.invoke(cli, ["remove", "requests", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show content with trailing newline, requests removed
    assert "django==3.0" in result.stdout
    assert "requests==2.25.1" not in result.stdout


def test_sort_preview_output_format(runner, tmp_path):
    """Test that sort command uses consistent output format in preview mode."""
    create_requirements_file(tmp_path, "project", "requests==2.25.1\ndjango==3.0\n")

    result = runner.invoke(cli, ["sort", "--preview", str(tmp_path)])

    # Should show file path
    assert "requirements.txt" in result.stdout

    # Should show sorted content with trailing newline
    lines = result.stdout.split("\n")
    content_lines = [
        line
        for line in lines
        if line.strip()
        and not ("\x1b[" in line or "requirements.txt" in line or "Previewing" in line)
    ]
    assert len(content_lines) >= 2
    # Should be sorted alphabetically
    assert "django==3.0" in result.stdout
    assert "requests==2.25.1" in result.stdout


def test_all_preview_commands_consistent_format(runner, tmp_path):
    """Test that all preview commands use consistent output format."""
    create_requirements_file(tmp_path, "project", "requests==2.25.1\ndjango==3.0\n")

    # Test all commands that support preview
    commands = [
        ["update", "requests", "2.30.0", "--preview", str(tmp_path)],
        ["add", "pytest", "--preview", str(tmp_path)],
        ["remove", "requests", "--preview", str(tmp_path)],
        ["sort", "--preview", str(tmp_path)],
    ]

    for cmd in commands:
        result = runner.invoke(cli, cmd)

        # All should show file path consistently
        assert "requirements.txt" in result.stdout, (
            f"Command {cmd[0]} missing file path"
        )

        # All should have successful exit code
        assert result.exit_code == 0, (
            f"Command {cmd[0]} failed with exit code {result.exit_code}"
        )
