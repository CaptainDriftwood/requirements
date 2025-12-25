"""Tests for package name validation."""

import click
import pytest

from src.main import validate_package_name


@pytest.mark.parametrize(
    "package_name",
    [
        "requests",
        "Django",
        "flask-restful",
        "my_package",
        "package123",
        "a",
        "a1",
        "numpy",
        "scikit-learn",
        "typing_extensions",
        "zope.interface",
        "A",
        "Z9",
    ],
)
def test_validate_valid_package_names(package_name: str) -> None:
    """Test that valid package names pass validation."""
    result = validate_package_name(package_name)
    assert result == package_name.strip()


@pytest.mark.parametrize(
    "package_name",
    [
        "  requests  ",  # With whitespace
        " Django",
        "flask ",
    ],
)
def test_validate_strips_whitespace(package_name: str) -> None:
    """Test that whitespace is stripped from package names."""
    result = validate_package_name(package_name)
    assert result == package_name.strip()


@pytest.mark.parametrize(
    "package_name,error_substring",
    [
        ("", "cannot be empty"),
        ("   ", "cannot be empty"),
        ("my package", "Invalid package name"),  # Contains space
        ("-package", "must start and end"),  # Starts with hyphen
        ("package-", "must start and end"),  # Ends with hyphen
        ("_package", "must start and end"),  # Starts with underscore
        ("package_", "must start and end"),  # Ends with underscore
        (".package", "must start and end"),  # Starts with period
        ("package.", "must start and end"),  # Ends with period
        ("my@package", "Invalid package name"),  # Contains @
        ("my!package", "Invalid package name"),  # Contains !
        ("my/package", "Invalid package name"),  # Contains /
    ],
)
def test_validate_invalid_package_names(
    package_name: str, error_substring: str
) -> None:
    """Test that invalid package names raise ClickException with appropriate message."""
    with pytest.raises(click.ClickException) as exc_info:
        validate_package_name(package_name)

    assert error_substring in str(exc_info.value)
