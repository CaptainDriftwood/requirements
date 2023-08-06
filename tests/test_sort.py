from typing import List

import pytest
from src.main import sort_packages


@pytest.fixture
def packages() -> List[str]:
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


def test_sort_with_locale(packages) -> None:
    result = sort_packages(packages, locale_="en_US.UTF-8")
    assert result == [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]


def test_sort_with_uk_locale(packages) -> None:
    result = sort_packages(packages, locale_="en_GB.UTF-8")
    assert result == [
        "# some comment",
        "./some_package",
        "apischema",
        "boto3",
        "python-dateutil",
        "requests",
    ]
