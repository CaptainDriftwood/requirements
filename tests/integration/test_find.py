import pathlib

from click.testing import CliRunner
from pyfakefs.fake_filesystem import FakeFilesystem

from requirements.main import find_package


class TestFindPackage:
    """Test find_package functionality"""

    def test_find_existing_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding an existing package in requirements.txt"""
        result = cli_runner.invoke(find_package, ["pytest", single_requirements_file])
        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_find_nonexistent_package(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding a non-existent package in requirements.txt"""
        result = cli_runner.invoke(
            find_package, ["nonexistent", single_requirements_file]
        )
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_find_package_verbose(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        """Test finding a package with verbose output"""
        result = cli_runner.invoke(
            find_package, ["pytest", single_requirements_file, "--verbose"]
        )
        assert result.exit_code == 0
        assert "requirements.txt" in result.output
        assert "pytest" in result.output

    def test_find_package_multiple_files(
        self, cli_runner: CliRunner, multiple_nested_directories: str
    ) -> None:
        """Test finding a package in multiple requirements files"""
        result = cli_runner.invoke(
            find_package, ["pytest", multiple_nested_directories]
        )
        assert result.exit_code == 0
        assert result.output.count("requirements.txt") == 4

    def test_find_package_with_git_url(
        self, cli_runner: CliRunner, fs: FakeFilesystem
    ) -> None:
        """Test finding a package specified as a git URL with egg fragment."""
        tmp_path = pathlib.Path("/fake/find-git-url")
        tmp_path.mkdir(parents=True)
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("git+https://github.com/user/mypackage.git#egg=mypackage\n")

        result = cli_runner.invoke(find_package, ["mypackage", str(tmp_path)])

        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_find_package_with_pep440_url(
        self, cli_runner: CliRunner, fs: FakeFilesystem
    ) -> None:
        """Test finding a package specified with PEP 440 URL syntax."""
        tmp_path = pathlib.Path("/fake/find-pep440")
        tmp_path.mkdir(parents=True)
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("mypackage @ https://example.com/mypackage-1.0.whl\n")

        result = cli_runner.invoke(find_package, ["mypackage", str(tmp_path)])

        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_find_package_with_github_repo_fallback(
        self, cli_runner: CliRunner, fs: FakeFilesystem
    ) -> None:
        """Test finding a package by GitHub repo name when no egg fragment."""
        tmp_path = pathlib.Path("/fake/find-github")
        tmp_path.mkdir(parents=True)
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("git+https://github.com/user/my-repo.git\n")

        result = cli_runner.invoke(find_package, ["my-repo", str(tmp_path)])

        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_find_package_url_verbose(
        self, cli_runner: CliRunner, fs: FakeFilesystem
    ) -> None:
        """Test finding a URL package with verbose output."""
        tmp_path = pathlib.Path("/fake/find-verbose")
        tmp_path.mkdir(parents=True)
        url_line = "git+https://github.com/user/repo.git@v1.0#egg=mypackage"
        req_file = tmp_path / "requirements.txt"
        req_file.write_text(f"{url_line}\n")

        result = cli_runner.invoke(
            find_package, ["mypackage", str(tmp_path), "--verbose"]
        )

        assert result.exit_code == 0
        assert "requirements.txt" in result.output
        assert url_line in result.output

    def test_find_package_url_not_found(
        self, cli_runner: CliRunner, fs: FakeFilesystem
    ) -> None:
        """Test that non-matching URL packages are not found."""
        tmp_path = pathlib.Path("/fake/find-not-found")
        tmp_path.mkdir(parents=True)
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("git+https://github.com/user/other.git#egg=other\n")

        result = cli_runner.invoke(find_package, ["mypackage", str(tmp_path)])

        assert result.exit_code == 0
        assert result.output.strip() == ""
