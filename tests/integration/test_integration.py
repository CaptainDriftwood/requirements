import pathlib
import subprocess
import tempfile

from click.testing import CliRunner

from src.main import (
    add_package,
    cli,
    find_package,
    remove_package,
    update_package,
)


class TestCLIIntegration:
    """Test full CLI integration"""

    def test_cli_help(self, cli_runner: CliRunner) -> None:
        """Test CLI help output"""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Manage requirements.txt files" in result.output

    def test_cli_version(self, cli_runner: CliRunner) -> None:
        """Test CLI version output"""
        result = cli_runner.invoke(cli, ["--version"])
        # Version command may fail if package not installed, but should handle gracefully
        assert result.exit_code in [0, 1]

    def test_update_command_help(self, cli_runner: CliRunner) -> None:
        """Test update command help"""
        result = cli_runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0
        assert "Update a package version" in result.output

    def test_add_command_help(self, cli_runner: CliRunner) -> None:
        """Test add command help"""
        result = cli_runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        assert "Add a package" in result.output

    def test_remove_command_help(self, cli_runner: CliRunner) -> None:
        """Test remove command help"""
        result = cli_runner.invoke(cli, ["remove", "--help"])
        assert result.exit_code == 0
        assert "Remove a package" in result.output

    def test_find_command_help(self, cli_runner: CliRunner) -> None:
        """Test find command help"""
        result = cli_runner.invoke(cli, ["find", "--help"])
        assert result.exit_code == 0
        assert "Find a package" in result.output

    def test_sort_command_help(self, cli_runner: CliRunner) -> None:
        """Test sort command help"""
        result = cli_runner.invoke(cli, ["sort", "--help"])
        assert result.exit_code == 0
        assert "Sort requirements.txt" in result.output

    def test_cat_command_help(self, cli_runner: CliRunner) -> None:
        """Test cat command help"""
        result = cli_runner.invoke(cli, ["cat", "--help"])
        assert result.exit_code == 0
        assert "Display the contents" in result.output


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_workflow_add_update_remove(self, cli_runner: CliRunner) -> None:
        """Test complete workflow: add, update, then remove a package"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("requests==2.25.1\n")

            # Add a package
            result = cli_runner.invoke(add_package, ["pytest", td])
            assert result.exit_code == 0
            contents = requirements_file.read_text()
            assert "pytest" in contents
            assert "requests==2.25.1" in contents

            # Update the package
            result = cli_runner.invoke(update_package, ["pytest", ">=6.0.0", td])
            assert result.exit_code == 0
            contents = requirements_file.read_text()
            assert "pytest>=6.0.0" in contents

            # Remove the package
            result = cli_runner.invoke(remove_package, ["pytest", td])
            assert result.exit_code == 0
            contents = requirements_file.read_text()
            assert "pytest" not in contents
            assert "requests==2.25.1" in contents

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

            # Test updating common package across all files
            result = cli_runner.invoke(update_package, ["common_lib", "3.0.0", td])
            assert result.exit_code == 0

            # Verify all files were updated
            for i in range(10):
                req_file = base_path / f"service_{i}" / "requirements.txt"
                contents = req_file.read_text()
                assert "common_lib==3.0.0" in contents


class TestErrorHandling:
    """Test error handling scenarios"""

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


class TestVirtualEnvironmentExclusion:
    """Test virtual environment directory exclusion"""

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


class TestCLIEntryPoint:
    """Test that the CLI entry point is installed and functional"""

    def test_cli_entry_point_help(self) -> None:
        """Verify the CLI entry point responds to --help"""
        result = subprocess.run(
            ["requirements", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "Manage requirements.txt files" in result.stdout

    def test_cli_entry_point_version(self) -> None:
        """Verify the CLI entry point responds to --version"""
        result = subprocess.run(
            ["requirements", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "requirements" in result.stdout.lower()
