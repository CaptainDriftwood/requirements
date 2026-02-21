import pathlib

from click.testing import CliRunner
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.main import add_package

# =============================================================================
# add_package tests
# =============================================================================


def test_add_new_package(cli_runner: CliRunner, single_requirements_file: str) -> None:
    """Test adding a new package to requirements.txt"""
    result = cli_runner.invoke(add_package, ["requests", single_requirements_file])
    assert result.exit_code == 0
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert "requests" in contents
    assert "boto3~=1.0.0" in contents
    assert "enhancement-models==1.0.0" in contents
    assert "pytest" in contents


def test_add_existing_package(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test adding an existing package to requirements.txt"""
    result = cli_runner.invoke(add_package, ["pytest", single_requirements_file])
    assert result.exit_code == 0
    assert "pytest already exists" in result.output
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


def test_add_package_with_preview(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test adding a package with preview flag"""
    result = cli_runner.invoke(
        add_package, ["requests", single_requirements_file, "--preview"]
    )
    assert result.exit_code == 0
    assert "Previewing changes" in result.output
    assert "requests" in result.output

    # Verify file unchanged
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


def test_add_package_multiple_files(
    cli_runner: CliRunner, multiple_nested_directories: str
) -> None:
    """Test adding a package to multiple requirements files"""
    result = cli_runner.invoke(add_package, ["requests", multiple_nested_directories])
    assert result.exit_code == 0

    for i in range(3):
        contents = (
            pathlib.Path(multiple_nested_directories)
            / f"directory{i}"
            / "requirements.txt"
        ).read_text()
        assert "requests" in contents


# =============================================================================
# Inline comments tests
# =============================================================================


def test_add_package_preserves_inline_comments(
    cli_runner: CliRunner, fs: FakeFilesystem
) -> None:
    """Test that adding a package preserves existing inline comments"""
    # Create a requirements.txt file with inline comments
    requirements_dir = pathlib.Path("/fake/add-comments")
    requirements_dir.mkdir(parents=True)
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    requirements_file.write_text(
        "django==3.2.0  # Web framework\npytest==6.2.5  # Testing framework\n"
    )

    # Add a new package
    result = cli_runner.invoke(
        add_package,
        ["requests", str(requirements_dir)],
    )

    assert result.exit_code == 0
    assert f"Updated {requirements_file}" in result.output

    # Check that the file was updated correctly and comments were preserved
    updated_content = requirements_file.read_text()
    assert updated_content == (
        "django==3.2.0  # Web framework\npytest==6.2.5  # Testing framework\nrequests\n"
    )


def test_add_package_preserves_inline_comments_preview_mode(
    cli_runner: CliRunner, fs: FakeFilesystem
) -> None:
    """Test that adding a package preserves inline comments in preview mode"""
    # Create a requirements.txt file with inline comments
    requirements_dir = pathlib.Path("/fake/add-comments-preview")
    requirements_dir.mkdir(parents=True)
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    initial_content = (
        "django==3.2.0  # Web framework\npytest==6.2.5  # Testing framework\n"
    )
    requirements_file.write_text(initial_content)

    # Add a new package in preview mode
    result = cli_runner.invoke(
        add_package,
        ["requests", str(requirements_dir), "--preview"],
    )

    assert result.exit_code == 0
    assert "Previewing changes" in result.output

    # Check that preview shows diff-style output with added package
    assert "+requests" in result.output

    # Verify that the file was NOT modified (preview mode)
    actual_content = requirements_file.read_text()
    assert actual_content == initial_content
