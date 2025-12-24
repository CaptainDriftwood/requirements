import pathlib
import tempfile

import pytest
from click.testing import CliRunner

from src.main import sort_packages, sort_requirements


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


def test_sort_with_no_locale(packages):
    # Use explicit C locale for deterministic cross-platform behavior
    result = sort_packages(packages, locale_="C")
    assert result == [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]


def test_sort_with_invalid_locale(packages: list[str]) -> None:
    """Test sorting with an invalid locale falls back to default sorting"""
    result = sort_packages(packages, locale_="invalid_locale")
    # Should fall back to default sorting (same as no locale)
    expected = [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]
    assert result == expected


def test_sort_empty_list() -> None:
    """Test sorting an empty list"""
    result = sort_packages([])
    assert result == []


def test_sort_single_package() -> None:
    """Test sorting a single package"""
    result = sort_packages(["single-package"])
    assert result == ["single-package"]


def test_sort_with_mixed_formats() -> None:
    """Test sorting packages with mixed version specifiers and formats"""
    packages = [
        "zpackage>=1.0.0",
        "apache==2.0.0",
        "boto3~=1.17.0",
        "# Development dependencies",
        "./local_package",
        "requests<3.0.0",
        "django!=2.0.0",
    ]
    # Use explicit C locale for deterministic cross-platform behavior
    result = sort_packages(packages, locale_="C")
    expected = [
        "# Development dependencies",
        "./local_package",
        "apache==2.0.0",
        "boto3~=1.17.0",
        "django!=2.0.0",
        "requests<3.0.0",
        "zpackage>=1.0.0",
    ]
    assert result == expected


def test_sort_with_comments_and_blank_lines() -> None:
    """Test sorting packages with comments and blank lines (legacy behavior)"""
    packages = [
        "zpackage",
        "# Main dependencies",
        "",
        "apache",
        "# Dev dependencies",
        "boto3",
        "",
    ]
    # Use explicit C locale for deterministic cross-platform behavior
    result = sort_packages(packages, preserve_comments=False, locale_="C")
    # Comments and blank lines should be sorted alphabetically too (legacy behavior)
    expected = [
        "",
        "",
        "# Dev dependencies",
        "# Main dependencies",
        "apache",
        "boto3",
        "zpackage",
    ]
    assert result == expected


def test_sort_with_comment_preservation() -> None:
    """Test sorting packages while preserving comment associations"""
    packages = [
        "# Main dependencies",
        "zpackage==1.0.0",
        "apache==2.0.0",
        "",
        "# Dev dependencies",
        "boto3==1.18.0",
        "zebra==0.5.0",
    ]
    result = sort_packages(packages, preserve_comments=True)
    # Comments should stay with their associated packages
    expected = [
        "# Main dependencies",
        "apache==2.0.0",
        "zpackage==1.0.0",
        "",
        "# Dev dependencies",
        "boto3==1.18.0",
        "zebra==0.5.0",
    ]
    assert result == expected


def test_sort_with_mixed_comments() -> None:
    """Test sorting with various comment patterns"""
    packages = [
        "# Header comment",
        "",
        "# Web frameworks",
        "zflask==2.0.0",
        "django==3.2.0",
        "",
        "# Database",
        "postgresql==12.0",
        "# ORM layer",
        "sqlalchemy==1.4.0",
        "",
        "# Utilities",
        "requests==2.26.0",
    ]
    result = sort_packages(packages, preserve_comments=True)
    expected = [
        "# Header comment",
        "",
        "# Web frameworks",
        "django==3.2.0",
        "zflask==2.0.0",
        "",
        "# Database",
        "# ORM layer",
        "postgresql==12.0",
        "sqlalchemy==1.4.0",
        "",
        "# Utilities",
        "requests==2.26.0",
    ]
    assert result == expected


def test_sort_preserves_exact_package_strings() -> None:
    """Test that sorting preserves exact package specification strings"""
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


@pytest.mark.parametrize(
    "locale_name",
    [
        "C",
        "POSIX",
    ],
)
def test_sort_with_c_posix_locales(packages: list[str], locale_name: str) -> None:
    """Test sorting with C and POSIX locales"""
    result = sort_packages(packages, locale_=locale_name)
    expected = [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]
    assert result == expected


@pytest.mark.parametrize(
    "locale_name",
    [
        "en_US.UTF-8",
        "en_GB.UTF-8",
    ],
)
def test_sort_with_utf8_locales(
    packages: list[str], locale_name: str, consistent_locale_collation
) -> None:
    """Test sorting with UTF-8 locales"""
    result = sort_packages(packages, locale_=locale_name, preserve_comments=False)
    expected = [
        "./some_package",
        "# some comment",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]
    assert result == expected


class TestSortRequirementsCommand:
    """Test sort_requirements CLI command functionality"""

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
