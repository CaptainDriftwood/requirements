from click.testing import CliRunner

from src.main import find_package


class TestFindPackage:
    """Test find_package functionality"""

    def test_find_existing_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding an existing package in requirements.txt"""
        result = cli_runner.invoke(find_package, ["pytest", single_requirements_file])
        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_find_nonexistent_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding a non-existent package in requirements.txt"""
        result = cli_runner.invoke(
            find_package, ["nonexistent", single_requirements_file]
        )
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_find_package_verbose(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding a package with verbose output"""
        result = cli_runner.invoke(
            find_package, ["pytest", single_requirements_file, "--verbose"]
        )
        assert result.exit_code == 0
        assert "requirements.txt" in result.output
        assert "pytest" in result.output

    def test_find_package_multiple_files(
        self, cli_runner: CliRunner, multiple_nested_directories: str
    ) -> None:
        """Test finding a package in multiple requirements files"""
        result = cli_runner.invoke(
            find_package, ["pytest", multiple_nested_directories]
        )
        assert result.exit_code == 0
        assert result.output.count("requirements.txt") == 4
