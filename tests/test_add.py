import pathlib

from click.testing import CliRunner
from src.main import add_package


class TestAddPackage:
    """Test add_package functionality"""

    def test_add_new_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test adding a new package to requirements.txt"""
        result = cli_runner.invoke(add_package, ["requests", single_requirements_file])
        assert result.exit_code == 0
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert "requests" in contents
        assert "boto3~=1.0.0" in contents
        assert "enhancement-models==1.0.0" in contents
        assert "pytest" in contents

    def test_add_existing_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test adding an existing package to requirements.txt"""
        result = cli_runner.invoke(add_package, ["pytest", single_requirements_file])
        assert result.exit_code == 0
        assert "pytest already exists" in result.output
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"

    def test_add_package_with_preview(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test adding a package with preview flag"""
        result = cli_runner.invoke(
            add_package, ["requests", single_requirements_file, "--preview"]
        )
        assert result.exit_code == 0
        assert "Previewing changes" in result.output
        assert "requests" in result.output

        # Verify file unchanged
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"

    def test_add_package_multiple_files(
        self, cli_runner: CliRunner, multiple_nested_directories: str
    ) -> None:
        """Test adding a package to multiple requirements files"""
        result = cli_runner.invoke(
            add_package, ["requests", multiple_nested_directories]
        )
        assert result.exit_code == 0

        for i in range(3):
            contents = (
                pathlib.Path(multiple_nested_directories)
                / f"directory{i}"
                / "requirements.txt"
            ).read_text()
            assert "requests" in contents
