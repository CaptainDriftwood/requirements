"""Tests for PyPI Simple API client."""

import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from requirements.pypi import (
    PyPIFetchError,
    SimpleAPIParser,
    _extract_version_from_filename,
    fetch_package_versions,
    fetch_with_fallback,
)

# =============================================================================
# SimpleAPIParser tests
# =============================================================================


def test_parser_parse_wheel_files() -> None:
    """Test parsing wheel file links."""
    html = """
    <a href="url">requests-2.28.0-py3-none-any.whl</a>
    <a href="url">requests-2.28.1-py3-none-any.whl</a>
    """
    parser = SimpleAPIParser()
    parser.feed(html)
    assert len(parser.files) == 2
    assert parser.files[0] == ("requests-2.28.0-py3-none-any.whl", False)
    assert parser.files[1] == ("requests-2.28.1-py3-none-any.whl", False)


def test_parser_parse_sdist_files() -> None:
    """Test parsing sdist file links."""
    html = """
    <a href="url">requests-2.28.0.tar.gz</a>
    <a href="url">requests-2.28.1.tar.gz</a>
    """
    parser = SimpleAPIParser()
    parser.feed(html)
    assert len(parser.files) == 2
    assert parser.files[0] == ("requests-2.28.0.tar.gz", False)
    assert parser.files[1] == ("requests-2.28.1.tar.gz", False)


def test_parser_parse_yanked_files() -> None:
    """Test parsing yanked file links."""
    html = """
    <a href="url">requests-2.28.0-py3-none-any.whl</a>
    <a href="url" data-yanked="security issue">requests-2.28.1-py3-none-any.whl</a>
    """
    parser = SimpleAPIParser()
    parser.feed(html)
    assert len(parser.files) == 2
    assert parser.files[0] == ("requests-2.28.0-py3-none-any.whl", False)
    assert parser.files[1] == ("requests-2.28.1-py3-none-any.whl", True)


def test_parser_parse_full_fixture(requests_simple_html: str) -> None:
    """Test parsing full PyPI Simple API HTML fixture."""
    parser = SimpleAPIParser()
    parser.feed(requests_simple_html)
    # Should have 10 files (5 versions x 2 formats each)
    assert len(parser.files) == 10
    # Check yanked versions are marked
    yanked_files = [f for f, is_yanked in parser.files if is_yanked]
    assert len(yanked_files) == 2  # 2.32.0 wheel and sdist


# =============================================================================
# Version extraction tests
# =============================================================================


@pytest.mark.parametrize(
    ("filename", "package", "expected"),
    [
        ("requests-2.28.0-py3-none-any.whl", "requests", "2.28.0"),
        ("requests-2.28.0.tar.gz", "requests", "2.28.0"),
        ("Django-4.2.0-py3-none-any.whl", "django", "4.2.0"),
        ("Django-4.2.0.tar.gz", "Django", "4.2.0"),
        ("my_package-1.0.0-py3-none-any.whl", "my-package", "1.0.0"),
        ("my-package-1.0.0.tar.gz", "my_package", "1.0.0"),
        ("boto3-1.26.100-py3-none-any.whl", "boto3", "1.26.100"),
        ("numpy-1.24.0-cp311-cp311-macosx_10_9_x86_64.whl", "numpy", "1.24.0"),
    ],
)
def test_extract_version_from_filename(
    filename: str, package: str, expected: str
) -> None:
    """Test extracting version from various filename formats."""
    result = _extract_version_from_filename(filename, package)
    assert result == expected


def test_extract_version_from_filename_no_match() -> None:
    """Test that non-matching filename returns None."""
    result = _extract_version_from_filename("other-1.0.0.tar.gz", "requests")
    assert result is None


# =============================================================================
# fetch_package_versions tests
# =============================================================================


def test_fetch_versions_from_fixture(mock_pypi_response: MagicMock) -> None:
    """Test fetching versions from PyPI fixture."""
    with patch("urllib.request.urlopen", return_value=mock_pypi_response):
        versions = fetch_package_versions("requests")

    # Should have 4 versions (2.32.0 is yanked and excluded)
    assert len(versions) == 4
    # Should be sorted newest first
    assert versions[0] == "2.32.3"
    assert versions[1] == "2.31.0"
    assert versions[2] == "2.28.1"
    assert versions[3] == "2.28.0"


def test_fetch_versions_include_yanked(mock_pypi_response: MagicMock) -> None:
    """Test fetching versions including yanked packages."""
    with patch("urllib.request.urlopen", return_value=mock_pypi_response):
        versions = fetch_package_versions("requests", include_yanked=True)

    # Should have 5 versions (including yanked 2.32.0)
    assert len(versions) == 5
    assert "2.32.0" in versions


def test_fetch_versions_custom_index(mock_pypi_response: MagicMock) -> None:
    """Test fetching versions from custom index URL."""
    with patch(
        "urllib.request.urlopen", return_value=mock_pypi_response
    ) as mock_urlopen:
        fetch_package_versions("requests", index_url="https://nexus.example.com/simple")

    # Verify the custom index URL was used
    call_args = mock_urlopen.call_args
    request = call_args[0][0]
    assert "nexus.example.com" in request.full_url


def test_fetch_versions_normalizes_package_name(mock_pypi_response: MagicMock) -> None:
    """Test that package names are normalized per PEP 503."""
    with patch(
        "urllib.request.urlopen", return_value=mock_pypi_response
    ) as mock_urlopen:
        fetch_package_versions("My_Package.Name")

    # Verify the package name was normalized (PEP 503)
    call_args = mock_urlopen.call_args
    request = call_args[0][0]
    assert "my-package-name" in request.full_url


# =============================================================================
# PyPIFetchError tests
# =============================================================================


def test_pypi_fetch_error_attributes() -> None:
    """Test PyPIFetchError stores URL and original error."""
    original = ValueError("original error")
    error = PyPIFetchError("https://example.com", original)

    assert error.url == "https://example.com"
    assert error.original_error is original
    assert "https://example.com" in str(error)
    assert "original error" in str(error)


# =============================================================================
# fetch_with_fallback tests
# =============================================================================


def test_fallback_returns_primary_on_success(mock_pypi_response: MagicMock) -> None:
    """Test that primary URL results are returned on success."""
    with patch("urllib.request.urlopen", return_value=mock_pypi_response):
        versions, url_used = fetch_with_fallback(
            "requests",
            index_url="https://primary.example.com/simple/",
            fallback_url="https://fallback.example.com/simple/",
        )

    assert len(versions) == 4
    assert url_used == "https://primary.example.com/simple/"


def test_fallback_uses_fallback_on_network_error(
    mock_pypi_response: MagicMock,
) -> None:
    """Test that fallback is used on network error."""

    def side_effect(request, **kwargs):
        if "primary" in request.full_url:
            raise urllib.error.URLError("Connection refused")
        return mock_pypi_response

    with patch("urllib.request.urlopen", side_effect=side_effect):
        versions, url_used = fetch_with_fallback(
            "requests",
            index_url="https://primary.example.com/simple/",
            fallback_url="https://fallback.example.com/simple/",
        )

    assert len(versions) == 4
    assert url_used == "https://fallback.example.com/simple/"


def test_fallback_uses_fallback_on_server_error(mock_pypi_response: MagicMock) -> None:
    """Test that fallback is used on HTTP 500 error."""

    def side_effect(request, **kwargs):
        if "primary" in request.full_url:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=500,
                msg="Internal Server Error",
                hdrs={},  # type: ignore[arg-type]
                fp=None,
            )
        return mock_pypi_response

    with patch("urllib.request.urlopen", side_effect=side_effect):
        versions, url_used = fetch_with_fallback(
            "requests",
            index_url="https://primary.example.com/simple/",
            fallback_url="https://fallback.example.com/simple/",
        )

    assert len(versions) == 4
    assert url_used == "https://fallback.example.com/simple/"


def test_fallback_no_fallback_on_404() -> None:
    """Test that 404 does NOT trigger fallback."""
    error = urllib.error.HTTPError(
        url="https://primary.example.com/simple/nonexistent/",
        code=404,
        msg="Not Found",
        hdrs={},  # type: ignore[arg-type]
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(PyPIFetchError) as exc_info:
            fetch_with_fallback(
                "nonexistent",
                index_url="https://primary.example.com/simple/",
                fallback_url="https://fallback.example.com/simple/",
            )

    assert "primary.example.com" in exc_info.value.url
    assert isinstance(exc_info.value.original_error, urllib.error.HTTPError)
    assert exc_info.value.original_error.code == 404


def test_fallback_raises_when_both_fail() -> None:
    """Test that error is raised when both URLs fail."""
    error = urllib.error.URLError("Connection refused")

    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(PyPIFetchError) as exc_info:
            fetch_with_fallback(
                "requests",
                index_url="https://primary.example.com/simple/",
                fallback_url="https://fallback.example.com/simple/",
            )

    assert "primary.example.com" in exc_info.value.url
    assert "fallback.example.com" in exc_info.value.url


def test_fallback_no_fallback_raises_on_error() -> None:
    """Test that error is raised when no fallback and primary fails."""
    error = urllib.error.URLError("Connection refused")

    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(PyPIFetchError):
            fetch_with_fallback(
                "requests",
                index_url="https://primary.example.com/simple/",
                fallback_url=None,
            )


def test_fallback_uses_default_index_when_none_provided(
    mock_pypi_response: MagicMock,
) -> None:
    """Test that default PyPI is used when no index URL provided."""
    with patch("urllib.request.urlopen", return_value=mock_pypi_response):
        versions, url_used = fetch_with_fallback("requests")

    assert len(versions) == 4
    assert url_used == "https://pypi.org/simple/"
