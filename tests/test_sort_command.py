import pathlib
import tempfile

from click.testing import CliRunner

from src.main import sort_requirements


class TestSortRequirements:
    """Test sort_requirements functionality"""

    def test_sort_requirements_file(self, cli_runner: CliRunner) -> None:
        """Test sorting a requirements file"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("zpackage\napache\nboto3\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0
            assert "Sorted" in result.output

            contents = requirements_file.read_text()
            assert contents == "apache\nboto3\nzpackage\n"

    def test_sort_already_sorted_file(self, cli_runner: CliRunner) -> None:
        """Test sorting an already sorted requirements file"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            # Create an already sorted file
            requirements_file.write_text("apache\nboto3\nzpackage\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0
            assert "already sorted" in result.output

    def test_sort_requirements_with_preview(self, cli_runner: CliRunner) -> None:
        """Test sorting requirements with preview flag"""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("zpackage\napache\nboto3\n")

            result = cli_runner.invoke(sort_requirements, [td, "--preview"])
            assert result.exit_code == 0
            assert "Previewing changes" in result.output

            # Verify file unchanged
            contents = requirements_file.read_text()
            assert contents == "zpackage\napache\nboto3\n"
