import os
import pathlib

from click.testing import CliRunner

from src.main import update_package


class TestPreviewChanges:
    """Test previewing changes against files"""

    def test_single_requirements_file(
        self, cli_runner: CliRunner, single_requirements_file: str
    ) -> None:
        result = cli_runner.invoke(
            update_package,
            [
                "pytest",
                "~=6.0.0",
                single_requirements_file,
                "--preview",
            ],
        )
        assert result.exit_code == 0
        assert (
            result.output == f"Previewing changes\n{single_requirements_file}/"
            f"requirements.txt\nboto3~=1.0.0\nenhancement-models==1.0.0\npytest~=6.0.0\n\n"
        )

        # assert that file contents are unchanged
        contents = (
            pathlib.Path(single_requirements_file) / "requirements.txt"
        ).read_text()
        assert contents == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"

    def test_multiple_requirements_files(
        self, cli_runner: CliRunner, multiple_nested_directories: str
    ) -> None:
        result = cli_runner.invoke(
            update_package,
            [
                "pytest",
                "~=6.0.0",
                multiple_nested_directories,
                "--preview",
            ],
        )
        assert result.exit_code == 0


def test_single_requirements_file_in_directory(
    single_requirements_file: str, cli_runner: CliRunner
) -> None:
    result = cli_runner.invoke(
        update_package, ["pytest", "~=6.0.0", single_requirements_file]
    )
    assert result.exit_code == 0
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==1.0.0\npytest~=6.0.0\n"


def test_multiple_requirements_files(
    cli_runner: CliRunner, multiple_nested_directories: str
) -> None:
    result = cli_runner.invoke(
        update_package, ["pytest", "~=6.0.0", multiple_nested_directories]
    )
    assert result.exit_code == 0
    for i in range(3):
        contents = (
            pathlib.Path(multiple_nested_directories)
            / f"directory{i}"
            / "requirements.txt"
        ).read_text()
        assert contents == "boto3~=1.0.0\nenhancement-models==1.0.0\npytest~=6.0.0\n"


def test_replace_package_with_hyphen(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test replacing a package with a hyphen in the name"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement_models",
            "==2.0.0",
            single_requirements_file,
        ],
    )
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement_models==2.0.0\npytest\n"


def test_replace_package_with_underscore(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test replacing a package with an underscore in the name"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "==2.0.0",
            single_requirements_file,
        ],
    )
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==2.0.0\npytest\n"


def test_multiple_paths_argument(
    cli_runner: CliRunner, multiple_nested_directories: str
) -> None:
    """Test passing in multiple paths to the CLI"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "==2.0.0",
            f"{multiple_nested_directories}/directory0/requirements.txt",
            f"{multiple_nested_directories}/directory1/requirements.txt",
        ],
    )
    for i in range(3):
        if i > 1:
            break
        contents = (
            pathlib.Path(multiple_nested_directories)
            / f"directory{i}"
            / "requirements.txt"
        ).read_text()
        assert contents == "boto3~=1.0.0\nenhancement-models==2.0.0\npytest\n"


def test_replace_without_paths(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test replacing a package without passing in paths"""

    # Change directory to parent directory of single_requirements_file
    # for the duration of this test
    current_directory = pathlib.Path.cwd()
    os.chdir(pathlib.Path(single_requirements_file).parent)

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "==2.0.0",
        ],
    )
    os.chdir(current_directory)
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==2.0.0\npytest\n"


def test_update_without_version_specifier(
    cli_runner: CliRunner, single_requirements_file: str
) -> None:
    """Test updating a package without passing in a version specifier"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "1.0.0",
            single_requirements_file,
        ],
    )
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==1.0.0\npytest\n"


def test_update_with_aws_sam_directory(
    cli_runner: CliRunner, single_requirements_file_with_aws_sam_build_directory: str
) -> None:
    """Test updating a package with an AWS SAM directory"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "5.0.0",
            single_requirements_file_with_aws_sam_build_directory,
        ],
    )
    contents = (
        pathlib.Path(single_requirements_file_with_aws_sam_build_directory)
        / "requirements.txt"
    ).read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==5.0.0\npytest\n"

    # also assert that the AWS SAM build directory is unchanged
    sam_build_directory = (
        pathlib.Path(single_requirements_file_with_aws_sam_build_directory)
        / ".aws-sam/build"
    )
    assert sam_build_directory.exists()
    assert len(list(sam_build_directory.iterdir())) == 1
    assert (sam_build_directory / "HelloWorldFunction" / "app.py").exists()
    assert (
        sam_build_directory / "HelloWorldFunction" / "requirements.txt"
    ).read_text() == "pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


def test_update_package_with_inline_comment(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test updating a package that has an inline comment on the same line"""
    # Create a requirements.txt file with inline comments
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    requirements_file.write_text(
        "django==3.2.0  # Web framework\n"
        "requests==2.26.0  # HTTP library\n"
        "pytest==6.2.5  # Testing framework\n"
    )

    # Update the requests package to a new version
    result = cli_runner.invoke(
        update_package,
        ["requests", "2.28.0", str(requirements_dir)],
    )

    assert result.exit_code == 0
    assert f"Updated {requirements_file}" in result.output

    # Check that the file was updated correctly and comments were preserved
    updated_content = requirements_file.read_text()
    assert updated_content == (
        "django==3.2.0  # Web framework\n"
        "pytest==6.2.5  # Testing framework\n"
        "requests==2.28.0  # HTTP library\n"
    )


def test_update_package_with_inline_comment_preview_mode(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test updating a package with inline comment in preview mode"""
    # Create a requirements.txt file with inline comments
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Write initial content with inline comments
    initial_content = (
        "django==3.2.0  # Web framework\n"
        "requests==2.26.0  # HTTP library for APIs\n"
        "pytest==6.2.5  # Testing framework\n"
    )
    requirements_file.write_text(initial_content)

    # Update the requests package in preview mode
    result = cli_runner.invoke(
        update_package,
        ["requests", "2.28.0", str(requirements_dir), "--preview"],
    )

    assert result.exit_code == 0
    assert "Previewing changes" in result.output

    # Check that preview shows the correct output
    assert "django==3.2.0  # Web framework" in result.output
    assert "pytest==6.2.5  # Testing framework" in result.output
    assert "requests==2.28.0  # HTTP library for APIs" in result.output

    # Verify that the file was NOT modified (preview mode)
    actual_content = requirements_file.read_text()
    assert actual_content == initial_content


def test_update_package_with_invalid_version_specifier(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test updating a package with invalid version specifier fails gracefully"""
    # Create a requirements.txt file
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"
    requirements_file.write_text("requests==2.26.0\n")

    # Test with various invalid version specifiers
    invalid_versions = [
        "==not.a.version",  # Invalid version format
        "==1.2.3..4",  # Double dots
        ">=",  # Missing version
        "~=abc",  # Non-numeric version
        "==1.2.3-",  # Trailing dash
        ">=1.2.3+",  # Trailing plus
    ]

    for invalid_version in invalid_versions:
        result = cli_runner.invoke(
            update_package,
            ["requests", invalid_version, str(requirements_dir)],
        )

        # Should exit with error for invalid version specifiers
        assert result.exit_code != 0, (
            f"Expected failure for invalid version: {invalid_version}"
        )
        assert "Invalid version specifier" in result.output or "Error" in result.output


def test_update_package_with_valid_version_specifiers(
    cli_runner: CliRunner, tmp_path: pathlib.Path
) -> None:
    """Test updating a package with various valid version specifiers"""
    # Create a requirements.txt file
    requirements_dir = tmp_path / "project"
    requirements_dir.mkdir()
    requirements_file = requirements_dir / "requirements.txt"

    # Test with various valid version specifiers
    valid_versions = [
        "==2.28.0",  # Basic equality
        ">=2.28.0",  # Greater than or equal
        "~=2.28.0",  # Compatible release
        "!=2.27.0",  # Not equal
        ">=1.0.0,<3.0.0",  # Multiple constraints
        "==2.28.0a1",  # Alpha release
        "==2.28.0b1",  # Beta release
        "==2.28.0rc1",  # Release candidate
        "==2.28.0.post1",  # Post release
        ">=1.0.dev0",  # Dev release
    ]

    for valid_version in valid_versions:
        # Reset file content for each test
        requirements_file.write_text("requests==2.26.0\n")

        result = cli_runner.invoke(
            update_package,
            ["requests", valid_version, str(requirements_dir)],
        )

        # Should succeed for valid version specifiers
        assert result.exit_code == 0, (
            f"Expected success for valid version: {valid_version}"
        )

        # Verify the file was updated correctly
        updated_content = requirements_file.read_text()
        assert f"requests{valid_version}" in updated_content
