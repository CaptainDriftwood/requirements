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
