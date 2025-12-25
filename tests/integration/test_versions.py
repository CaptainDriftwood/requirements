"""Tests for the versions command."""

import subprocess

from click.testing import CliRunner
from pytest_mock import MockerFixture

from src.main import _parse_pip_index_versions, cli


class TestParsePipIndexVersions:
    """Test the pip index versions output parser."""

    def test_parse_standard_output(self) -> None:
        """Test parsing standard pip index versions output."""
        output = """requests (2.32.5)
Available versions: 2.32.5, 2.32.4, 2.32.3, 2.32.2, 2.32.1"""

        latest, versions = _parse_pip_index_versions(output)

        assert latest == "2.32.5"
        assert versions == ["2.32.5", "2.32.4", "2.32.3", "2.32.2", "2.32.1"]

    def test_parse_many_versions(self) -> None:
        """Test parsing output with many versions."""
        output = """django (5.0.0)
Available versions: 5.0.0, 4.2.8, 4.2.7, 4.2.6, 4.2.5, 4.2.4, 4.2.3, 4.2.2, 4.2.1, 4.2.0, 4.1.13, 4.1.12"""

        latest, versions = _parse_pip_index_versions(output)

        assert latest == "5.0.0"
        assert len(versions) == 12
        assert versions[0] == "5.0.0"
        assert versions[-1] == "4.1.12"

    def test_parse_empty_output(self) -> None:
        """Test parsing empty output."""
        output = ""

        latest, versions = _parse_pip_index_versions(output)

        assert latest is None
        assert versions == []

    def test_parse_no_versions_line(self) -> None:
        """Test parsing output without versions line."""
        output = """requests (2.32.5)"""

        latest, versions = _parse_pip_index_versions(output)

        assert latest == "2.32.5"
        assert versions == []


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
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test successful versions query with mocked subprocess."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=0,
            stdout="requests (2.32.5)\nAvailable versions: 2.32.5, 2.32.4, 2.32.3, 2.32.2, 2.32.1, 2.32.0, 2.31.0, 2.30.0, 2.29.0, 2.28.2, 2.28.1, 2.28.0\n",
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 0
        assert "requests" in result.output
        assert "2.32.5" in result.output
        assert "showing 10 of 12 versions" in result.output

    def test_versions_command_all_flag(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command with --all flag."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=0,
            stdout="requests (2.32.5)\nAvailable versions: 2.32.5, 2.32.4, 2.32.3, 2.32.2, 2.32.1, 2.32.0, 2.31.0, 2.30.0, 2.29.0, 2.28.2, 2.28.1, 2.28.0\n",
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "requests", "--all"])

        assert result.exit_code == 0
        assert "requests" in result.output
        # All 12 versions should be shown
        assert "2.28.0" in result.output
        # No "showing X of Y" hint
        assert "showing" not in result.output.lower() or "use --all" not in result.output

    def test_versions_command_limit_flag(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command with --limit flag."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=0,
            stdout="requests (2.32.5)\nAvailable versions: 2.32.5, 2.32.4, 2.32.3, 2.32.2, 2.32.1, 2.32.0\n",
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "requests", "--limit", "3"])

        assert result.exit_code == 0
        assert "2.32.5" in result.output
        assert "showing 3 of 6 versions" in result.output

    def test_versions_command_index_url(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command with --index-url flag."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "mypackage", "--index-url", "https://nexus.example.com/simple"],
            returncode=0,
            stdout="mypackage (1.0.0)\nAvailable versions: 1.0.0, 0.9.0, 0.8.0\n",
            stderr="",
        )

        result = cli_runner.invoke(
            cli,
            ["versions", "mypackage", "--index-url", "https://nexus.example.com/simple"],
        )

        assert result.exit_code == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args[1]["args"] if "args" in mock_run.call_args[1] else mock_run.call_args[0][0]
        assert "--index-url" in call_args
        assert "https://nexus.example.com/simple" in call_args

    def test_versions_command_package_not_found(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command when package is not found."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "nonexistent-package-xyz"],
            returncode=1,
            stdout="",
            stderr="ERROR: No matching distribution found for nonexistent-package-xyz",
        )

        result = cli_runner.invoke(cli, ["versions", "nonexistent-package-xyz"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_versions_command_pip_not_found(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command when pip is not installed."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.side_effect = FileNotFoundError("pip not found")

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "pip not found" in result.output.lower()

    def test_versions_fewer_than_limit(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command when there are fewer versions than limit."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "small-package"],
            returncode=0,
            stdout="small-package (1.0.0)\nAvailable versions: 1.0.0, 0.9.0, 0.8.0\n",
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "small-package"])

        assert result.exit_code == 0
        assert "1.0.0" in result.output
        assert "0.9.0" in result.output
        assert "0.8.0" in result.output
        # No "showing X of Y" hint when all versions are shown
        assert "use --all" not in result.output

    def test_versions_command_old_pip_version(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command with old pip version that doesn't support index versions."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=1,
            stdout="",
            stderr="ERROR: unknown command 'index versions'",
        )

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "pip 21.2+" in result.output

    def test_versions_command_generic_error(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command with a generic pip error."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=1,
            stdout="",
            stderr="ERROR: Some unexpected error occurred",
        )

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "Failed to query versions" in result.output

    def test_versions_command_no_versions_found(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command when pip returns success but no versions."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=0,
            stdout="requests ()\n",  # Malformed output with no versions
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 1
        assert "No versions found" in result.output

    def test_versions_command_without_latest(
        self, cli_runner: CliRunner, mocker: MockerFixture
    ) -> None:
        """Test versions command when output doesn't include latest version."""
        mock_run = mocker.patch("src.main.subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["pip", "index", "versions", "requests"],
            returncode=0,
            stdout="Available versions: 2.32.5, 2.32.4, 2.32.3\n",  # No (latest) line
            stderr="",
        )

        result = cli_runner.invoke(cli, ["versions", "requests"])

        assert result.exit_code == 0
        assert "requests" in result.output
        assert "2.32.5" in result.output
        # Should not show "latest:" since it wasn't in output
        assert "latest:" not in result.output
