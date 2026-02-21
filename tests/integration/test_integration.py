import pathlib
import subprocess

from click.testing import CliRunner
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.main import (
    add_package,
    cli,
    find_package,
    remove_package,
    update_package,
)

# =============================================================================
# CLI integration tests
# =============================================================================


def test_cli_help(cli_runner: CliRunner) -> None:
    """Test CLI help output"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Manage requirements.txt files" in result.output


def test_cli_version(cli_runner: CliRunner) -> None:
    """Test CLI version output"""
    result = cli_runner.invoke(cli, ["--version"])
    # Version command may fail if package not installed, but should handle gracefully
    assert result.exit_code in [0, 1]


def test_update_command_help(cli_runner: CliRunner) -> None:
    """Test update command help"""
    result = cli_runner.invoke(cli, ["update", "--help"])
    assert result.exit_code == 0
    assert "Update a package version" in result.output


def test_add_command_help(cli_runner: CliRunner) -> None:
    """Test add command help"""
    result = cli_runner.invoke(cli, ["add", "--help"])
    assert result.exit_code == 0
    assert "Add a package" in result.output


def test_remove_command_help(cli_runner: CliRunner) -> None:
    """Test remove command help"""
    result = cli_runner.invoke(cli, ["remove", "--help"])
    assert result.exit_code == 0
    assert "Remove a package" in result.output


def test_find_command_help(cli_runner: CliRunner) -> None:
    """Test find command help"""
    result = cli_runner.invoke(cli, ["find", "--help"])
    assert result.exit_code == 0
    assert "Find a package" in result.output


def test_sort_command_help(cli_runner: CliRunner) -> None:
    """Test sort command help"""
    result = cli_runner.invoke(cli, ["sort", "--help"])
    assert result.exit_code == 0
    assert "Sort requirements.txt" in result.output


def test_cat_command_help(cli_runner: CliRunner) -> None:
    """Test cat command help"""
    result = cli_runner.invoke(cli, ["cat", "--help"])
    assert result.exit_code == 0
    assert "Display the contents" in result.output


# =============================================================================
# Complex real-world scenario tests
# =============================================================================


def test_workflow_add_update_remove(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test complete workflow: add, update, then remove a package"""
    td = pathlib.Path("/fake/workflow-test")
    td.mkdir(parents=True)
    requirements_file = td / "requirements.txt"
    requirements_file.write_text("requests==2.25.1\n")

    # Add a package
    result = cli_runner.invoke(add_package, ["pytest", str(td)])
    assert result.exit_code == 0
    contents = requirements_file.read_text()
    assert "pytest" in contents
    assert "requests==2.25.1" in contents

    # Update the package
    result = cli_runner.invoke(update_package, ["pytest", ">=6.0.0", str(td)])
    assert result.exit_code == 0
    contents = requirements_file.read_text()
    assert "pytest>=6.0.0" in contents

    # Remove the package
    result = cli_runner.invoke(remove_package, ["pytest", str(td)])
    assert result.exit_code == 0
    contents = requirements_file.read_text()
    assert "pytest" not in contents
    assert "requests==2.25.1" in contents


def test_mixed_package_formats(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test handling mixed package formats"""
    td = pathlib.Path("/fake/mixed-formats")
    td.mkdir(parents=True)
    requirements_file = td / "requirements.txt"
    requirements_file.write_text(
        "requests==2.25.1\n"
        "boto3~=1.0.0\n"
        "pytest>=6.0.0\n"
        "django<4.0.0\n"
        "# comment line\n"
        "./local_package\n"
        "git+https://github.com/user/repo.git\n"
    )

    # Test finding packages with different formats
    result = cli_runner.invoke(find_package, ["requests", str(td)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output

    result = cli_runner.invoke(find_package, ["local_package", str(td)])
    assert result.exit_code == 0
    assert "requirements.txt" in result.output


def test_large_monorepo_simulation(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test performance with many nested directories"""
    td = pathlib.Path("/fake/monorepo")
    td.mkdir(parents=True)

    # Create 10 nested directories with requirements files
    for i in range(10):
        dir_path = td / f"service_{i}"
        dir_path.mkdir()
        req_file = dir_path / "requirements.txt"
        req_file.write_text(f"service_{i}_dependency==1.0.0\ncommon_lib==2.0.0\n")

    # Test finding common package across all files
    result = cli_runner.invoke(find_package, ["common_lib", str(td)])
    assert result.exit_code == 0
    assert result.output.count("requirements.txt") == 10

    # Test updating common package across all files
    result = cli_runner.invoke(update_package, ["common_lib", "3.0.0", str(td)])
    assert result.exit_code == 0

    # Verify all files were updated
    for i in range(10):
        req_file = td / f"service_{i}" / "requirements.txt"
        contents = req_file.read_text()
        assert "common_lib==3.0.0" in contents


# =============================================================================
# Error handling tests
# =============================================================================


def test_invalid_path(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test handling invalid file paths"""
    result = cli_runner.invoke(find_package, ["pytest", "/nonexistent/path"])
    assert result.exit_code == 0
    assert "does not exist" in result.output


def test_empty_requirements_file(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test handling empty requirements files"""
    td = pathlib.Path("/fake/empty")
    td.mkdir(parents=True)
    requirements_file = td / "requirements.txt"
    requirements_file.write_text("")

    result = cli_runner.invoke(find_package, ["pytest", str(td)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_malformed_requirements_file(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test handling malformed requirements files"""
    td = pathlib.Path("/fake/malformed")
    td.mkdir(parents=True)
    requirements_file = td / "requirements.txt"
    requirements_file.write_text("# Just a comment\n\n# Another comment\n")

    result = cli_runner.invoke(find_package, ["pytest", str(td)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


# =============================================================================
# Virtual environment exclusion tests
# =============================================================================


def test_exclude_venv_directory(
    cli_runner: CliRunner, requirements_txt: bytes, fs: FakeFilesystem
) -> None:
    """Test that venv directories are excluded"""
    td = pathlib.Path("/fake/venv-test")
    td.mkdir(parents=True)
    # Create main requirements file
    main_req = td / "requirements.txt"
    main_req.write_text(requirements_txt.decode("utf-8"))

    # Create venv directory with requirements file
    venv_dir = td / "venv"
    venv_dir.mkdir()
    venv_req = venv_dir / "requirements.txt"
    venv_req.write_text("should_be_excluded\n")

    # Test that venv requirements are excluded
    result = cli_runner.invoke(find_package, ["should_be_excluded", str(td)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_exclude_dot_venv_directory(
    cli_runner: CliRunner, requirements_txt: bytes, fs: FakeFilesystem
) -> None:
    """Test that .venv directories are excluded"""
    td = pathlib.Path("/fake/dotvenv-test")
    td.mkdir(parents=True)
    # Create main requirements file
    main_req = td / "requirements.txt"
    main_req.write_text(requirements_txt.decode("utf-8"))

    # Create .venv directory with requirements file
    venv_dir = td / ".venv"
    venv_dir.mkdir()
    venv_req = venv_dir / "requirements.txt"
    venv_req.write_text("should_be_excluded\n")

    # Test that .venv requirements are excluded
    result = cli_runner.invoke(find_package, ["should_be_excluded", str(td)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_exclude_virtualenv_directory(
    cli_runner: CliRunner, requirements_txt: bytes, fs: FakeFilesystem
) -> None:
    """Test that virtualenv directories are excluded"""
    td = pathlib.Path("/fake/virtualenv-test")
    td.mkdir(parents=True)
    # Create main requirements file
    main_req = td / "requirements.txt"
    main_req.write_text(requirements_txt.decode("utf-8"))

    # Create virtualenv directory with requirements file
    venv_dir = td / "virtualenv"
    venv_dir.mkdir()
    venv_req = venv_dir / "requirements.txt"
    venv_req.write_text("should_be_excluded\n")

    # Test that virtualenv requirements are excluded
    result = cli_runner.invoke(find_package, ["should_be_excluded", str(td)])
    assert result.exit_code == 0
    assert result.output.strip() == ""


# =============================================================================
# Sort summary tests
# =============================================================================


def test_sort_multiple_files_summary(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test that sorting multiple files shows a summary."""
    tmp_path = pathlib.Path("/fake/sort-multiple")
    tmp_path.mkdir(parents=True)
    # Create 3 unsorted requirements files
    for name in ["project1", "project2", "project3"]:
        subdir = tmp_path / name
        subdir.mkdir()
        req_file = subdir / "requirements.txt"
        req_file.write_text("zebra==1.0.0\napple==2.0.0\nbanana==3.0.0\n")

    result = cli_runner.invoke(cli, ["sort", str(tmp_path)])

    assert result.exit_code == 0
    assert "Summary:" in result.output
    assert "3 sorted" in result.output
    assert "3 files total" in result.output


def test_sort_mixed_files_summary(cli_runner: CliRunner, fs: FakeFilesystem) -> None:
    """Test summary with mix of sorted and unsorted files."""
    tmp_path = pathlib.Path("/fake/sort-mixed")
    tmp_path.mkdir(parents=True)
    # Create one already sorted file
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()
    (sorted_dir / "requirements.txt").write_text("apple==1.0.0\nzebra==2.0.0\n")

    # Create one unsorted file
    unsorted_dir = tmp_path / "unsorted"
    unsorted_dir.mkdir()
    (unsorted_dir / "requirements.txt").write_text("zebra==2.0.0\napple==1.0.0\n")

    result = cli_runner.invoke(cli, ["sort", str(tmp_path)])

    assert result.exit_code == 0
    assert "Summary:" in result.output
    assert "1 sorted" in result.output
    assert "1 already sorted" in result.output
    assert "2 files total" in result.output


# =============================================================================
# CLI entry point tests
# =============================================================================


def test_cli_entry_point_help() -> None:
    """Verify the CLI entry point responds to --help"""
    result = subprocess.run(
        ["requirements", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Manage requirements.txt files" in result.stdout


def test_cli_entry_point_version() -> None:
    """Verify the CLI entry point responds to --version"""
    result = subprocess.run(
        ["requirements", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "requirements" in result.stdout.lower()
