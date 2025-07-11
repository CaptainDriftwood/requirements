import pathlib

from click.testing import CliRunner

from src.main import remove_package


class TestRemovePackage:
    """Test remove_package functionality"""

    def test_remove_existing_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test removing an existing package from requirements.txt"""
        result = cli_runner.invoke(remove_package, ["pytest", single_requirements_file])
        assert result.exit_code == 0
        assert "Removed pytest" in result.output
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert "pytest" not in contents
        assert "boto3~=1.0.0" in contents
        assert "enhancement-models==1.0.0" in contents

    def test_remove_nonexistent_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test removing a non-existent package from requirements.txt"""
        result = cli_runner.invoke(
            remove_package, ["nonexistent", single_requirements_file]
        )
        assert result.exit_code == 0
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"

    def test_remove_package_with_preview(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test removing a package with preview flag"""
        # Store original contents before preview
        original_contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()

        result = cli_runner.invoke(
            remove_package, ["pytest", single_requirements_file, "--preview"]
        )
        assert result.exit_code == 0
        assert "Previewing changes" in result.output
        # After preview, pytest should be removed from the preview output
        assert "boto3~=1.0.0" in result.output
        assert "enhancement-models==1.0.0" in result.output

        # File should remain unchanged in preview mode
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert contents == original_contents
        assert "pytest" in contents  # pytest should still be in the file

    def test_remove_package_multiple_files(
        self, cli_runner: CliRunner, multiple_nested_directories: str
    ) -> None:
        """Test removing a package from multiple requirements files"""
        result = cli_runner.invoke(
            remove_package, ["pytest", multiple_nested_directories]
        )
        assert result.exit_code == 0

        for i in range(3):
            contents = (
                pathlib.Path(multiple_nested_directories)
                / f"directory{i}"
                / "requirements.txt"
            ).read_text()
            assert "pytest" not in contents


def test_remove_package_preserves_inline_comments(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test that removing a package preserves inline comments on remaining packages"""
    # Create a requirements.txt file with inline comments
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    requirements_file.write_text(
        "django==3.2.0  # Web framework\n"
        "requests==2.26.0  # HTTP library\n"
        "pytest==6.2.5  # Testing framework\n"
    )

    # Remove the requests package
    result = cli_runner.invoke(
        remove_package,
        ["requests", str(requirements_dir)],
    )

    assert result.exit_code == 0
    assert f"Removed requests from {requirements_file}" in result.output

    # Check that the file was updated correctly and comments were preserved
    updated_content = requirements_file.read_text()
    assert updated_content == (
        "django==3.2.0  # Web framework\npytest==6.2.5  # Testing framework\n"
    )


def test_remove_package_preserves_inline_comments_preview_mode(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test that removing a package preserves inline comments in preview mode"""
    # Create a requirements.txt file with inline comments
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    initial_content = (
        "django==3.2.0  # Web framework\n"
        "requests==2.26.0  # HTTP library for APIs\n"
        "pytest==6.2.5  # Testing framework\n"
    )
    requirements_file.write_text(initial_content)

    # Remove the requests package in preview mode
    result = cli_runner.invoke(
        remove_package,
        ["requests", str(requirements_dir), "--preview"],
    )

    assert result.exit_code == 0
    assert "Previewing changes" in result.output

    # Check that preview shows the correct output with preserved comments
    assert "django==3.2.0  # Web framework" in result.output
    assert "pytest==6.2.5  # Testing framework" in result.output
    # requests should not be in the preview output
    assert "requests==2.26.0  # HTTP library for APIs" not in result.output

    # Verify that the file was NOT modified (preview mode)
    actual_content = requirements_file.read_text()
    assert actual_content == initial_content


def test_remove_package_with_inline_comment(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test that removing a package that has an inline comment works correctly"""
    # Create a requirements.txt file with inline comments
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    requirements_file.write_text(
        "django==3.2.0  # Web framework\n"
        "requests==2.26.0  # HTTP library to be removed\n"
        "pytest==6.2.5  # Testing framework\n"
    )

    # Remove the requests package (which has an inline comment)
    result = cli_runner.invoke(
        remove_package,
        ["requests", str(requirements_dir)],
    )

    assert result.exit_code == 0
    assert f"Removed requests from {requirements_file}" in result.output

    # Check that the package and its comment are both removed
    updated_content = requirements_file.read_text()
    assert updated_content == (
        "django==3.2.0  # Web framework\npytest==6.2.5  # Testing framework\n"
    )
    # Verify the removed package and its comment are gone
    assert "requests" not in updated_content
    assert "HTTP library to be removed" not in updated_content
