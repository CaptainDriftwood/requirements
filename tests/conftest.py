import pathlib
import tempfile
from typing import Generator

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    yield CliRunner()


@pytest.fixture
def requirements_txt() -> bytes:
    return b"pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


@pytest.fixture
def single_requirements_file(requirements_txt) -> Generator[str, None, None]:
    """Single temporary directory with a requirements.txt file"""

    with tempfile.TemporaryDirectory() as td:
        directory = pathlib.Path(td)
        requirements_file = directory / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
        yield td


@pytest.fixture
def multiple_nested_directories(requirements_txt) -> Generator[str, None, None]:
    """
    Multiple temporary nested directories with
    a single requirements.txt file in each
    """

    with tempfile.TemporaryDirectory() as td:
        for i in range(3):
            directory = pathlib.Path(td) / f"directory{i}"
            directory.mkdir()
            requirements_file = directory / "requirements.txt"
            requirements_file.write_text(requirements_txt.decode("utf-8"))
        requirements_file = pathlib.Path(td) / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
        yield td


@pytest.fixture
def single_requirements_file_with_aws_sam_build_directory(
    requirements_txt,
) -> Generator[str, None, None]:
    """
    A single requirements.txt file that is adjacent to an AWS SAM build directory (.aws-sam/build),
    which should be ignored by the CLI. The AWS SAM build directory contains a single directory called
    "HelloWorldFunction" with a single file called "app.py" and a single requirements.txt file with the same
    contents as the single requirements.txt file.
    """

    with tempfile.TemporaryDirectory() as td:
        directory = pathlib.Path(td)
        requirements_file = directory / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
        sam_build_directory = directory / ".aws-sam/build"
        sam_build_directory.mkdir(parents=True)
        hello_world_function_directory = sam_build_directory / "HelloWorldFunction"
        hello_world_function_directory.mkdir()
        app_file = hello_world_function_directory / "app.py"
        app_file.write_text("def handler(event, context):\n    return 'Hello world'")
        requirements_file = hello_world_function_directory / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
        yield td
