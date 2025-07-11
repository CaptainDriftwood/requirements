from pathlib import Path

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def runner():
    """Click test runner with stderr separation."""
    return CliRunner(mix_stderr=False)


def create_requirements_file(
    base_path: Path, subdir: str, content: str, read_only: bool = False
) -> Path:
    """Create a requirements.txt file with given content, optionally read-only."""
    project_dir = base_path / subdir
    project_dir.mkdir(exist_ok=True)

    file_path = project_dir / "requirements.txt"
    file_path.write_text(content)

    if read_only:
        file_path.chmod(0o444)

    return file_path


def test_update_all_files_read_only(runner, tmp_path):
    """Test update command when all files are read-only."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(cli, ["update", "requests", "2.30.0", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning messages for read-only files
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"
    assert file2.read_text() == "flask==1.1.4\nrequests==2.25.1\n"


def test_update_subset_files_read_only(runner, tmp_path):
    """Test update command when subset of files are read-only."""
    # Create mixed files - one read-only, one writable
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=False
    )

    result = runner.invoke(cli, ["update", "requests", "2.30.0", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning for read-only file only
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Should show success message for writable file
    assert "Updated" in result.stdout

    # Read-only file should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"

    # Writable file should be updated
    updated_content = file2.read_text()
    assert "requests==2.30.0" in updated_content


def test_update_preview_mode_no_warnings(runner, tmp_path):
    """Test update command with --preview flag doesn't show read-only warnings."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(
        cli, ["update", "requests", "2.30.0", "--preview", str(tmp_path)]
    )

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages in preview mode
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show preview output
    assert "Previewing changes" in result.stdout

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"
    assert file2.read_text() == "flask==1.1.4\nrequests==2.25.1\n"


def test_add_all_files_read_only(runner, tmp_path):
    """Test add command when all files are read-only."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\n", read_only=True
    )

    result = runner.invoke(cli, ["add", "pytest", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning messages for read-only files
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\n"
    assert file2.read_text() == "flask==1.1.4\n"


def test_add_subset_files_read_only(runner, tmp_path):
    """Test add command when subset of files are read-only."""
    # Create mixed files - one read-only, one writable
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\n", read_only=False
    )

    result = runner.invoke(cli, ["add", "pytest", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning for read-only file only
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Should show success message for writable file
    assert "Updated" in result.stdout

    # Read-only file should remain unchanged
    assert file1.read_text() == "django==3.0\n"

    # Writable file should be updated
    updated_content = file2.read_text()
    assert "pytest" in updated_content


def test_add_preview_mode_no_warnings(runner, tmp_path):
    """Test add command with --preview flag doesn't show read-only warnings."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\n", read_only=True
    )

    result = runner.invoke(cli, ["add", "pytest", "--preview", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages in preview mode
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show preview output
    assert "Previewing changes" in result.stdout

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\n"
    assert file2.read_text() == "flask==1.1.4\n"


def test_remove_all_files_read_only(runner, tmp_path):
    """Test remove command when all files are read-only."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(cli, ["remove", "requests", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning messages for read-only files
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"
    assert file2.read_text() == "flask==1.1.4\nrequests==2.25.1\n"


def test_remove_subset_files_read_only(runner, tmp_path):
    """Test remove command when subset of files are read-only."""
    # Create mixed files - one read-only, one writable
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=False
    )

    result = runner.invoke(cli, ["remove", "requests", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning for read-only file only
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Should show success message for writable file
    assert "Removed" in result.stdout

    # Read-only file should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"

    # Writable file should be updated (requests removed)
    updated_content = file2.read_text()
    assert "requests" not in updated_content
    assert "flask==1.1.4" in updated_content


def test_remove_preview_mode_no_warnings(runner, tmp_path):
    """Test remove command with --preview flag doesn't show read-only warnings."""
    # Create read-only files
    file1 = create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(cli, ["remove", "requests", "--preview", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages in preview mode
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show preview output
    assert "Previewing changes" in result.stdout

    # Files should remain unchanged
    assert file1.read_text() == "django==3.0\nrequests==2.25.1\n"
    assert file2.read_text() == "flask==1.1.4\nrequests==2.25.1\n"


def test_sort_all_files_read_only(runner, tmp_path):
    """Test sort command when all files are read-only."""
    # Create read-only files with unsorted content
    file1 = create_requirements_file(
        tmp_path, "project1", "requests==2.25.1\ndjango==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "pytest==6.0\nflask==1.1.4\n", read_only=True
    )

    result = runner.invoke(cli, ["sort", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning messages for read-only files
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Files should remain unchanged (unsorted)
    assert file1.read_text() == "requests==2.25.1\ndjango==3.0\n"
    assert file2.read_text() == "pytest==6.0\nflask==1.1.4\n"


def test_sort_subset_files_read_only(runner, tmp_path):
    """Test sort command when subset of files are read-only."""
    # Create mixed files - one read-only, one writable, both unsorted
    file1 = create_requirements_file(
        tmp_path, "project1", "requests==2.25.1\ndjango==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "pytest==6.0\nflask==1.1.4\n", read_only=False
    )

    result = runner.invoke(cli, ["sort", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should show warning for read-only file only
    assert "Warning:" in result.stderr
    assert "read-only" in result.stderr

    # Should show success message for writable file
    assert "Sorted" in result.stdout

    # Read-only file should remain unchanged (unsorted)
    assert file1.read_text() == "requests==2.25.1\ndjango==3.0\n"

    # Writable file should be sorted
    updated_content = file2.read_text()
    lines = updated_content.strip().split("\n")
    assert lines[0] == "flask==1.1.4"
    assert lines[1] == "pytest==6.0"


def test_sort_preview_mode_no_warnings(runner, tmp_path):
    """Test sort command with --preview flag doesn't show read-only warnings."""
    # Create read-only files with unsorted content
    file1 = create_requirements_file(
        tmp_path, "project1", "requests==2.25.1\ndjango==3.0\n", read_only=True
    )
    file2 = create_requirements_file(
        tmp_path, "project2", "pytest==6.0\nflask==1.1.4\n", read_only=True
    )

    result = runner.invoke(cli, ["sort", "--preview", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages in preview mode
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show preview output
    assert "Previewing changes" in result.stdout

    # Files should remain unchanged
    assert file1.read_text() == "requests==2.25.1\ndjango==3.0\n"
    assert file2.read_text() == "pytest==6.0\nflask==1.1.4\n"


def test_find_read_only_files_no_warnings(runner, tmp_path):
    """Test find command with read-only files doesn't show warnings (read-only operation)."""
    # Create read-only files
    create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(cli, ["find", "requests", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages (find is read-only)
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show found files
    assert "requirements.txt" in result.stdout


def test_cat_read_only_files_no_warnings(runner, tmp_path):
    """Test cat command with read-only files doesn't show warnings (read-only operation)."""
    # Create read-only files
    create_requirements_file(
        tmp_path, "project1", "django==3.0\nrequests==2.25.1\n", read_only=True
    )
    create_requirements_file(
        tmp_path, "project2", "flask==1.1.4\nrequests==2.25.1\n", read_only=True
    )

    result = runner.invoke(cli, ["cat", str(tmp_path)])

    # Should complete without crashing
    assert result.exit_code == 0

    # Should NOT show warning messages (cat is read-only)
    assert "Warning:" not in result.stderr
    assert "read-only" not in result.stderr

    # Should show file contents
    assert "django==3.0" in result.stdout
    assert "flask==1.1.4" in result.stdout
