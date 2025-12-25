import pathlib
import tempfile

import pytest
from click.testing import CliRunner

from src.main import sort_requirements
from src.sorting import sort_packages


@pytest.fixture
def packages() -> list[str]:
    return [
        "boto3",
        "apischema",
        "python-dateutil",
        "./some_package",
        "requests",
        "# some comment",
    ]


def test_sort_basic(packages: list[str]) -> None:
    """Test basic sorting with C locale (ASCII) ordering."""
    result = sort_packages(packages)
    # Comments are filtered out, packages sorted, path refs at end
    assert result == [
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
        "./some_package",
    ]


def test_sort_empty_list() -> None:
    """Test sorting an empty list."""
    result = sort_packages([])
    assert result == []


def test_sort_single_package() -> None:
    """Test sorting a single package."""
    result = sort_packages(["single-package"])
    assert result == ["single-package"]


def test_sort_with_mixed_formats() -> None:
    """Test sorting packages with mixed version specifiers and formats."""
    packages = [
        "zpackage>=1.0.0",
        "apache==2.0.0",
        "boto3~=1.17.0",
        "# Development dependencies",
        "./local_package",
        "requests<3.0.0",
        "django!=2.0.0",
    ]
    result = sort_packages(packages)
    # Comments filtered, packages sorted by name, path refs at end
    expected = [
        "apache==2.0.0",
        "boto3~=1.17.0",
        "django!=2.0.0",
        "requests<3.0.0",
        "zpackage>=1.0.0",
        "./local_package",
    ]
    assert result == expected


def test_sort_filters_out_comments() -> None:
    """Test that standalone comments are filtered out."""
    packages = [
        "zpackage",
        "# Main dependencies",
        "",
        "apache",
        "# Dev dependencies",
        "boto3",
        "",
    ]
    result = sort_packages(packages)
    # Comments and blank lines should be filtered out
    expected = [
        "apache",
        "boto3",
        "zpackage",
    ]
    assert result == expected


def test_sort_preserves_inline_comments() -> None:
    """Test that inline comments on package lines are preserved."""
    packages = [
        "zpackage==1.0.0  # pinned for security",
        "apache==2.0.0",
        "boto3==1.18.0  # required for AWS",
    ]
    result = sort_packages(packages)
    expected = [
        "apache==2.0.0",
        "boto3==1.18.0  # required for AWS",
        "zpackage==1.0.0  # pinned for security",
    ]
    assert result == expected


def test_sort_preserves_exact_package_strings() -> None:
    """Test that sorting preserves exact package specification strings."""
    packages = [
        "package-z[extra]==1.0.0",
        "package-a>=2.0.0,<3.0.0",
        "package-m~=1.5.0",
    ]
    result = sort_packages(packages)
    expected = [
        "package-a>=2.0.0,<3.0.0",
        "package-m~=1.5.0",
        "package-z[extra]==1.0.0",
    ]
    assert result == expected


def test_sort_path_references_at_end() -> None:
    """Test that path references are placed at the end."""
    packages = [
        "./local_package",
        "zpackage",
        "../shared_lib",
        "apache",
        "-e ./dev_package",
        "boto3",
        "-e ../another_lib",
    ]
    result = sort_packages(packages)
    expected = [
        "apache",
        "boto3",
        "zpackage",
        "./local_package",
        "../shared_lib",
        "-e ./dev_package",
        "-e ../another_lib",
    ]
    assert result == expected


def test_sort_case_sensitive() -> None:
    """Test that sorting is case-sensitive (C locale / ASCII order)."""
    packages = [
        "Zpackage",
        "apache",
        "Apache",
        "BOTO3",
        "boto3",
    ]
    result = sort_packages(packages)
    # C locale: uppercase before lowercase (A-Z: 65-90, a-z: 97-122)
    expected = [
        "Apache",
        "BOTO3",
        "Zpackage",
        "apache",
        "boto3",
    ]
    assert result == expected


class TestSortRequirementsCommand:
    """Test sort_requirements CLI command functionality."""

    def test_sort_requirements_file(self, cli_runner: CliRunner) -> None:
        """Test sorting a requirements file."""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("zpackage\napache\nboto3\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0
            assert "Sorted" in result.output

            contents = requirements_file.read_text()
            assert contents == "apache\nboto3\nzpackage\n"

    def test_sort_already_sorted_file(self, cli_runner: CliRunner) -> None:
        """Test sorting an already sorted requirements file."""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("apache\nboto3\nzpackage\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0
            assert "already sorted" in result.output

    def test_sort_requirements_with_preview(self, cli_runner: CliRunner) -> None:
        """Test sorting requirements with preview flag."""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("zpackage\napache\nboto3\n")

            result = cli_runner.invoke(sort_requirements, [td, "--preview"])
            assert result.exit_code == 0
            assert "Previewing changes" in result.output

            # Verify file unchanged
            contents = requirements_file.read_text()
            assert contents == "zpackage\napache\nboto3\n"

    def test_sort_removes_comments(self, cli_runner: CliRunner) -> None:
        """Test that sorting removes standalone comments."""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("# Header\nzpackage\n# Comment\napache\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0

            contents = requirements_file.read_text()
            assert contents == "apache\nzpackage\n"

    def test_sort_preserves_inline_comments(self, cli_runner: CliRunner) -> None:
        """Test that sorting preserves inline comments."""
        with tempfile.TemporaryDirectory() as td:
            requirements_file = pathlib.Path(td) / "requirements.txt"
            requirements_file.write_text("zpackage==1.0.0  # pinned\napache==2.0.0\n")

            result = cli_runner.invoke(sort_requirements, [td])
            assert result.exit_code == 0

            contents = requirements_file.read_text()
            assert contents == "apache==2.0.0\nzpackage==1.0.0  # pinned\n"
