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
                "pytest~=6.0.0",
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
    current_directory = os.getcwd()
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
