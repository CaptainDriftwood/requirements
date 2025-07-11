import pathlib
import tempfile

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


class TestFindPackageVirtualEnvironmentExclusion:
    """Test find_package virtual environment directory exclusion"""

    def test_exclude_venv_directory(
        self, cli_runner: CliRunner, requirements_txt: bytes
    ) -> None:
        """Test that venv directories are excluded"""
        with tempfile.TemporaryDirectory() as td:
            # Create main requirements file
            main_req = pathlib.Path(td) / "requirements.txt"
            main_req.write_text(requirements_txt.decode("utf-8"))

            # Create venv directory with requirements file
            venv_dir = pathlib.Path(td) / "venv"
            venv_dir.mkdir()
            venv_req = venv_dir / "requirements.txt"
            venv_req.write_text("should_be_excluded\n")

            # Test that venv requirements are excluded
            result = cli_runner.invoke(find_package, ["should_be_excluded", td])
            assert result.exit_code == 0
            assert result.output.strip() == ""

    def test_exclude_dot_venv_directory(
        self, cli_runner: CliRunner, requirements_txt: bytes
    ) -> None:
        """Test that .venv directories are excluded"""
        with tempfile.TemporaryDirectory() as td:
            # Create main requirements file
            main_req = pathlib.Path(td) / "requirements.txt"
            main_req.write_text(requirements_txt.decode("utf-8"))

            # Create .venv directory with requirements file
            venv_dir = pathlib.Path(td) / ".venv"
            venv_dir.mkdir()
            venv_req = venv_dir / "requirements.txt"
            venv_req.write_text("should_be_excluded\n")

            # Test that .venv requirements are excluded
            result = cli_runner.invoke(find_package, ["should_be_excluded", td])
            assert result.exit_code == 0
            assert result.output.strip() == ""

    def test_exclude_virtualenv_directory(
        self, cli_runner: CliRunner, requirements_txt: bytes
    ) -> None:
        """Test that virtualenv directories are excluded"""
        with tempfile.TemporaryDirectory() as td:
            # Create main requirements file
            main_req = pathlib.Path(td) / "requirements.txt"
            main_req.write_text(requirements_txt.decode("utf-8"))

            # Create virtualenv directory with requirements file
            venv_dir = pathlib.Path(td) / "virtualenv"
            venv_dir.mkdir()
            venv_req = venv_dir / "requirements.txt"
            venv_req.write_text("should_be_excluded\n")

            # Test that virtualenv requirements are excluded
            result = cli_runner.invoke(find_package, ["should_be_excluded", td])
            assert result.exit_code == 0
            assert result.output.strip() == ""


class TestFindPackageErrorHandling:
    """Test find_package error handling scenarios"""

    def test_invalid_path(self, cli_runner: CliRunner) -> None:
        """Test handling invalid file paths"""
        result = cli_runner.invoke(find_package, ["pytest", "/nonexistent/path"])
        assert result.exit_code == 0
        assert "does not exist" in result.output

    def test_empty_requirements_file(self, cli_runner: CliRunner) -> None:
        """Test handling empty requirements files"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("")

            result = cli_runner.invoke(find_package, ["pytest", td])
            assert result.exit_code == 0
            assert result.output.strip() == ""

    def test_malformed_requirements_file(self, cli_runner: CliRunner) -> None:
        """Test handling malformed requirements files"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("# Just a comment\n\n# Another comment\n")

            result = cli_runner.invoke(find_package, ["pytest", td])
            assert result.exit_code == 0
            assert result.output.strip() == ""


class TestFindPackageComplexScenarios:
    """Test find_package complex real-world scenarios"""

    def test_mixed_package_formats(self, cli_runner: CliRunner) -> None:
        """Test handling mixed package formats"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
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
            result = cli_runner.invoke(find_package, ["requests", td])
            assert result.exit_code == 0
            assert "requirements.txt" in result.output

            result = cli_runner.invoke(find_package, ["local_package", td])
            assert result.exit_code == 0
            assert "requirements.txt" in result.output

    def test_large_monorepo_simulation(self, cli_runner: CliRunner) -> None:
        """Test performance with many nested directories"""
        with tempfile.TemporaryDirectory() as td:
            base_path = pathlib.Path(td)

            # Create 10 nested directories with requirements files
            for i in range(10):
                dir_path = base_path / f"service_{i}"
                dir_path.mkdir()
                req_file = dir_path / "requirements.txt"
                req_file.write_text(
                    f"service_{i}_dependency==1.0.0\ncommon_lib==2.0.0\n"
                )

            # Test finding common package across all files
            result = cli_runner.invoke(find_package, ["common_lib", td])
            assert result.exit_code == 0
            assert result.output.count("requirements.txt") == 10
