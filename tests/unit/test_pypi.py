"""Tests for PyPI Simple API client."""

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from requirements.pypi import (
    SimpleAPIParser,
    _extract_version_from_filename,
    fetch_package_versions,
)


@pytest.fixture
def requests_simple_html() -> str:
    """Load the requests package Simple API HTML fixture."""
    fixture_path = (
        pathlib.Path(__file__).parent.parent / "fixtures" / "pypi_simple_requests.html"
    )
    return fixture_path.read_text()


class TestSimpleAPIParser:
    """Tests for the HTML parser."""

    def test_parse_wheel_files(self) -> None:
        html = """
        <a href="url">requests-2.28.0-py3-none-any.whl</a>
        <a href="url">requests-2.28.1-py3-none-any.whl</a>
        """
        parser = SimpleAPIParser()
        parser.feed(html)
        assert len(parser.files) == 2
        assert parser.files[0] == ("requests-2.28.0-py3-none-any.whl", False)
        assert parser.files[1] == ("requests-2.28.1-py3-none-any.whl", False)

    def test_parse_sdist_files(self) -> None:
        html = """
        <a href="url">requests-2.28.0.tar.gz</a>
        <a href="url">requests-2.28.1.tar.gz</a>
        """
        parser = SimpleAPIParser()
        parser.feed(html)
        assert len(parser.files) == 2
        assert parser.files[0] == ("requests-2.28.0.tar.gz", False)
        assert parser.files[1] == ("requests-2.28.1.tar.gz", False)

    def test_parse_yanked_files(self) -> None:
        html = """
        <a href="url">requests-2.28.0-py3-none-any.whl</a>
        <a href="url" data-yanked="security issue">requests-2.28.1-py3-none-any.whl</a>
        """
        parser = SimpleAPIParser()
        parser.feed(html)
        assert len(parser.files) == 2
        assert parser.files[0] == ("requests-2.28.0-py3-none-any.whl", False)
        assert parser.files[1] == ("requests-2.28.1-py3-none-any.whl", True)

    def test_parse_full_fixture(self, requests_simple_html: str) -> None:
        parser = SimpleAPIParser()
        parser.feed(requests_simple_html)
        # Should have 10 files (5 versions x 2 formats each)
        assert len(parser.files) == 10
        # Check yanked versions are marked
        yanked_files = [f for f, is_yanked in parser.files if is_yanked]
        assert len(yanked_files) == 2  # 2.32.0 wheel and sdist


class TestExtractVersionFromFilename:
    """Tests for version extraction from filenames."""

    @pytest.mark.parametrize(
        "filename,package,expected",
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
    def test_extract_version(self, filename: str, package: str, expected: str) -> None:
        result = _extract_version_from_filename(filename, package)
        assert result == expected

    def test_extract_version_no_match(self) -> None:
        result = _extract_version_from_filename("other-1.0.0.tar.gz", "requests")
        assert result is None


class TestFetchPackageVersions:
    """Tests for fetching package versions."""

    def test_fetch_versions_from_fixture(self, requests_simple_html: str) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            versions = fetch_package_versions("requests")

        # Should have 4 versions (2.32.0 is yanked and excluded)
        assert len(versions) == 4
        # Should be sorted newest first
        assert versions[0] == "2.32.3"
        assert versions[1] == "2.31.0"
        assert versions[2] == "2.28.1"
        assert versions[3] == "2.28.0"

    def test_fetch_versions_include_yanked(self, requests_simple_html: str) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            versions = fetch_package_versions("requests", include_yanked=True)

        # Should have 5 versions (including yanked 2.32.0)
        assert len(versions) == 5
        assert "2.32.0" in versions

    def test_fetch_versions_custom_index(self, requests_simple_html: str) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            fetch_package_versions(
                "requests", index_url="https://nexus.example.com/simple"
            )

        # Verify the custom index URL was used
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "nexus.example.com" in request.full_url

    def test_fetch_versions_normalizes_package_name(
        self, requests_simple_html: str
    ) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            fetch_package_versions("My_Package.Name")

        # Verify the package name was normalized (PEP 503)
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "my-package-name" in request.full_url
