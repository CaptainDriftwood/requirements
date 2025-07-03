import pytest

from src.main import sort_packages


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
    result = sort_packages(packages)
    assert result == [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]


def test_sort_with_locale(packages: list[str]) -> None:
    result = sort_packages(packages, locale_="en_US.UTF-8")
    assert result == [
        "./some_package",
        "# some comment",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]


def test_sort_with_uk_locale(packages: list[str]) -> None:
    result = sort_packages(packages, locale_="en_GB.UTF-8")
    assert result == [
        "./some_package",
        "# some comment",
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
    result = sort_packages(packages)
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
    """Test sorting packages with comments and blank lines"""
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
    # Comments and blank lines should be sorted alphabetically too
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
def test_sort_with_utf8_locales(packages: list[str], locale_name: str) -> None:
    """Test sorting with UTF-8 locales"""
    result = sort_packages(packages, locale_=locale_name)
    expected = [
        "./some_package",
        "# some comment",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]
    assert result == expected
