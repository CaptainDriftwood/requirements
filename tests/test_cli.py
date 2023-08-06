import os
import pathlib

import pytest
from src.main import (
    cat_requirements,
    check_package_name,
    gather_requirements_files,
    update_package,
)


class TestGatherRequirementsFiles:
    """Test functionality when locating requirements.txt files"""

    def test_single_requirements_file(self, single_requirements_file) -> None:
        filepath = pathlib.Path(single_requirements_file)
        files = gather_requirements_files([filepath])
        assert len(files) == 1

    def test_multiple_requirements_files(self, multiple_nested_directories) -> None:
        filepath = pathlib.Path(multiple_nested_directories)
        files = gather_requirements_files([filepath])
        assert len(files) == 4


def test_single_requirements_file_in_directory(
    single_requirements_file, cli_runner
) -> None:
    result = cli_runner.invoke(
        update_package, ["pytest", "~=6.0.0", single_requirements_file]
    )
    assert result.exit_code == 0
    contents = (pathlib.Path(single_requirements_file) / "requirements.txt").read_text()
    assert contents == "boto3~=1.0.0\nenhancement-models==1.0.0\npytest~=6.0.0\n"


def test_multiple_requirements_files(cli_runner, multiple_nested_directories) -> None:
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


class TestPreviewChanges:
    """Test previewing changes against files"""

    def test_single_requirements_file(
        self, cli_runner, single_requirements_file
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
        self, cli_runner, multiple_nested_directories
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


@pytest.mark.parametrize(
    "package_name, line, expected",
    [
        # Direct matches
        ("example", "example", True),
        ("example-package", "example_package", True),
        # With versions
        ("example", "example==1.2.3", True),
        ("example-package", "example_package>=1.2.3", True),
        ("example==1.2.3", "example==1.2.3", True),
        ("example==1.3.0", "example==1.2.3", False),
        # Local paths
        ("mypackage", "./mypackage", True),
        ("mypackage", "../another_dir/mypackage", True),
        ("mypackage", "../../mypackage", True),
        ("mypackage", "./another_dir/mypackage_1.2.3.tar.gz", True),
        # Non-matches
        ("example", "example_other", False),
        ("example-package", "example_other_package", False),
        ("mypackage", "./another-package", False),
        # Version specifiers with non-matching packages
        ("example", "example_other>=1.2.3", False),
        # Edge cases with underscore and dash differences
        ("example-package", "example_package>=1.2.3", True),
        ("example_package", "example-package==1.2.3", True),
        # Testing for package names with version specifiers
        ("example", "example[extra]==1.2.3", False),
        ("example_package", "example-package[extra]>=1.2.3", False),
        ("example-package", "example_package[extra]==1.2.3", False),
    ],
)
def test_check_package_name(package_name, line, expected) -> None:
    assert check_package_name(package_name, line) == expected


def test_cat_requirements(cli_runner, single_requirements_file) -> None:
    result = cli_runner.invoke(cat_requirements, [single_requirements_file])
    assert result.exit_code == 0
    assert (
        result.output
        == f"{single_requirements_file}/requirements.txt\npytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n\n"
    )


def test_replace_package_with_hyphen(cli_runner, single_requirements_file) -> None:
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


def test_replace_package_with_underscore(cli_runner, single_requirements_file):
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


def test_multiple_paths_argument(cli_runner, multiple_nested_directories) -> None:
    """Test passing in multiple paths to the CLI"""

    cli_runner.invoke(
        update_package,
        [
            "enhancement-models",
            "==2.0.0",
            f"{multiple_nested_directories}/directory0/requirements.txt  {multiple_nested_directories}/directory1/requirements.txt",  # noqa
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


def test_replace_without_paths(cli_runner, single_requirements_file) -> None:
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


def test_update_without_version_specifier(cli_runner, single_requirements_file) -> None:
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
    cli_runner, single_requirements_file_with_aws_sam_build_directory
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
