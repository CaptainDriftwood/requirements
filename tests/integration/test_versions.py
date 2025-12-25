"""Tests for the versions command."""

import pathlib
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def requests_simple_html() -> str:
    """Load the requests package Simple API HTML fixture."""
    fixture_path = (
        pathlib.Path(__file__).parent.parent / "fixtures" / "pypi_simple_requests.html"
    )
    return fixture_path.read_text()


class TestVersionsCommand:
    """Test the versions CLI command."""

    def test_versions_command_help(self, cli_runner: CliRunner) -> None:
        """Test that --help works for versions command."""
        result = cli_runner.invoke(cli, ["versions", "--help"])
        assert result.exit_code == 0
        assert "Show available versions" in result.output
        assert "--all" in result.output
        assert "--limit" in result.output
        assert "--index-url" in result.output

    def test_versions_command_success(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test successful versions query with mocked HTTP response."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 0
        assert "requests" in result.output
        assert "2.32.3" in result.output  # Latest version
        assert "latest" in result.output

    def test_versions_command_all_flag(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test versions command with --all flag."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "requests", "--all"])

        assert result.exit_code == 0
        assert "requests" in result.output
        # All 4 non-yanked versions should be shown
        assert "2.32.3" in result.output
        assert "2.31.0" in result.output
        assert "2.28.1" in result.output
        assert "2.28.0" in result.output
        # No "showing X of Y" hint
        assert "use --all" not in result.output

    def test_versions_command_limit_flag(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test versions command with --limit flag."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "requests", "--limit", "2"])

        assert result.exit_code == 0
        assert "2.32.3" in result.output
        assert "showing 2 of 4 versions" in result.output

    def test_versions_command_index_url(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test versions command with --index-url flag."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            result = cli_runner.invoke(
                cli,
                [
                    "versions",
                    "requests",
                    "--index-url",
                    "https://nexus.example.com/simple",
                ],
            )

        assert result.exit_code == 0
        # Verify the custom index URL was used
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        assert "nexus.example.com" in request.full_url

    def test_versions_command_package_not_found(self, cli_runner: CliRunner) -> None:
        """Test versions command when package is not found."""
        error = urllib.error.HTTPError(
            url="https://pypi.org/simple/nonexistent/",
            code=404,
            msg="Not Found",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=error):
            result = cli_runner.invoke(cli, ["versions", "nonexistent-package-xyz"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_versions_command_network_error(self, cli_runner: CliRunner) -> None:
        """Test versions command with network error."""
        error = urllib.error.URLError("Connection refused")

        with patch("urllib.request.urlopen", side_effect=error):
            result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "Network error" in result.output

    def test_versions_fewer_than_limit(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test versions command when there are fewer versions than limit."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 0
        # We have 4 versions, default limit is 10, so no "use --all" hint
        assert "use --all" not in result.output

    def test_versions_excludes_yanked(
        self, cli_runner: CliRunner, requests_simple_html: str
    ) -> None:
        """Test that yanked versions are excluded by default."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "requests", "--all"])

        assert result.exit_code == 0
        # 2.32.0 is yanked and should not appear
        assert "2.32.0" not in result.output
        # Other versions should appear
        assert "2.32.3" in result.output
        assert "2.31.0" in result.output

    def test_versions_command_http_error(self, cli_runner: CliRunner) -> None:
        """Test versions command with HTTP error (not 404)."""
        error = urllib.error.HTTPError(
            url="https://pypi.org/simple/requests/",
            code=500,
            msg="Internal Server Error",
            hdrs={},  # type: ignore[arg-type]
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=error):
            result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "HTTP error" in result.output

    def test_versions_no_versions_found(self, cli_runner: CliRunner) -> None:
        """Test versions command when no versions are found."""
        empty_html = """
        <!DOCTYPE html>
        <html><body><h1>Links for empty-package</h1></body></html>
        """
        mock_response = MagicMock()
        mock_response.read.return_value = empty_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = cli_runner.invoke(cli, ["versions", "empty-package"])

        assert result.exit_code == 1
        assert "No versions found" in result.output

    def test_versions_one_per_line_flag(
        self,
        cli_runner: CliRunner,
        requests_simple_html: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test versions command with -1/--one-per-line flag."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *args, **kwargs: mock_response
        )

        result = cli_runner.invoke(cli, ["versions", "requests", "-1"])

        assert result.exit_code == 0
        # Each version should be on its own line
        lines = result.output.strip().split("\n")
        # First line is the package header, then versions
        assert "2.32.3" in lines[1]
        assert "2.31.0" in lines[2]
        # Should not have comma-separated output
        assert "Available versions:" not in result.output

    def test_versions_one_per_line_long_flag(
        self,
        cli_runner: CliRunner,
        requests_simple_html: str,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test versions command with --one-per-line long flag."""
        mock_response = MagicMock()
        mock_response.read.return_value = requests_simple_html.encode("utf-8")
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr(
            "urllib.request.urlopen", lambda *args, **kwargs: mock_response
        )

        result = cli_runner.invoke(cli, ["versions", "requests", "--one-per-line"])

        assert result.exit_code == 0
        # Should not have comma-separated output
        assert "Available versions:" not in result.output
        # Versions should be on separate lines
        assert "2.32.3\n" in result.output
