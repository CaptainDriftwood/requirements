import pathlib
from collections.abc import Generator

import pytest
from click.testing import CliRunner
from pyfakefs.fake_filesystem import FakeFilesystem


@pytest.fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    yield CliRunner()


@pytest.fixture
def requirements_txt() -> bytes:
    return b"pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


@pytest.fixture
def single_requirements_file(fs: FakeFilesystem, requirements_txt: bytes) -> str:
    """Single temporary directory with a requirements.txt file"""
    directory = pathlib.Path("/fake/project")
    directory.mkdir(parents=True)
    requirements_file = directory / "requirements.txt"
    requirements_file.write_text(requirements_txt.decode("utf-8"))
    return str(directory)


@pytest.fixture
def multiple_nested_directories(fs: FakeFilesystem, requirements_txt: bytes) -> str:
    """
    Multiple temporary nested directories with
    a single requirements.txt file in each
    """
    base = pathlib.Path("/fake/monorepo")
    base.mkdir(parents=True)
    for i in range(3):
        directory = base / f"directory{i}"
        directory.mkdir()
        requirements_file = directory / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
    requirements_file = base / "requirements.txt"
    requirements_file.write_text(requirements_txt.decode("utf-8"))
    return str(base)


@pytest.fixture
def single_requirements_file_with_aws_sam_build_directory(
    fs: FakeFilesystem,
    requirements_txt: bytes,
) -> str:
    """
    A single requirements.txt file that is adjacent to an AWS SAM build directory (.aws-sam/build),
    which should be ignored by the CLI. The AWS SAM build directory contains a single directory called
    "HelloWorldFunction" with a single file called "app.py" and a single requirements.txt file with the same
    contents as the single requirements.txt file.
    """
    directory = pathlib.Path("/fake/sam-project")
    directory.mkdir(parents=True)
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
    return str(directory)


@pytest.fixture
def requirements_txt_with_comments() -> bytes:
    """Requirements file with comments and blank lines"""
    return b"""# Production dependencies
requests==2.25.1
boto3~=1.17.0

# Development dependencies
pytest>=6.0.0
black==21.0.0

# Optional dependencies
# django>=3.0.0
"""


@pytest.fixture
def complex_requirements_txt() -> bytes:
    """Complex requirements file with various package formats"""
    return b"""# Main dependencies
requests==2.25.1
boto3~=1.17.0,!=1.17.5
django>=3.0.0,<4.0.0
numpy[extra]==1.20.0

# Development dependencies
pytest>=6.0.0
black!=21.5b0

# Local packages
./local_package
../shared_lib

# VCS dependencies
git+https://github.com/user/repo.git@v1.0
git+https://github.com/user/repo.git#egg=package

# Comments and blank lines

# More packages
click
"""


@pytest.fixture
def empty_requirements_file(fs: FakeFilesystem) -> str:
    """Empty requirements.txt file"""
    directory = pathlib.Path("/fake/empty-project")
    directory.mkdir(parents=True)
    requirements_file = directory / "requirements.txt"
    requirements_file.write_text("")
    return str(directory)


@pytest.fixture
def requirements_with_errors(fs: FakeFilesystem) -> str:
    """Requirements file with malformed entries"""
    directory = pathlib.Path("/fake/errors-project")
    directory.mkdir(parents=True)
    requirements_file = directory / "requirements.txt"
    requirements_file.write_text(
        "valid_package==1.0.0\n"
        "# This is a comment\n"
        "\n"  # blank line
        "another_valid>=2.0.0\n"
        "# Another comment\n"
    )
    return str(directory)


@pytest.fixture
def create_requirements_file(fs: FakeFilesystem):
    """Factory fixture to create requirements.txt files with given content.

    Args:
        base_path: Base directory path (typically a Path in the fake filesystem)
        subdir: Subdirectory name to create
        content: Content to write to requirements.txt
        read_only: If True, make the file read-only (default: False)

    Returns:
        Path to the created requirements.txt file
    """

    def _create(
        base_path: pathlib.Path,
        subdir: str,
        content: str,
        read_only: bool = False,
    ) -> pathlib.Path:
        project_dir = base_path / subdir
        project_dir.mkdir(parents=True, exist_ok=True)
        file_path = project_dir / "requirements.txt"
        file_path.write_text(content)
        if read_only:
            file_path.chmod(0o444)
        return file_path

    return _create


@pytest.fixture
def multilevel_nested_directories(fs: FakeFilesystem) -> str:
    """Multiple levels of nested directories with requirements files"""
    base = pathlib.Path("/fake/multilevel")
    base.mkdir(parents=True)

    # Create nested structure: base/level1/level2/level3
    for level1 in ["service_a", "service_b"]:
        level1_path = base / level1
        level1_path.mkdir()
        req1 = level1_path / "requirements.txt"
        req1.write_text(
            f"# {level1} requirements\n{level1}_package==1.0.0\ncommon==1.0.0\n"
        )

        for level2 in ["api", "worker"]:
            level2_path = level1_path / level2
            level2_path.mkdir()
            req2 = level2_path / "requirements.txt"
            req2.write_text(
                f"# {level1}_{level2} requirements\n{level1}_{level2}_package==1.0.0\ncommon==1.0.0\n"
            )

            for level3 in ["src", "tests"]:
                level3_path = level2_path / level3
                level3_path.mkdir()
                req3 = level3_path / "requirements.txt"
                req3.write_text(
                    f"# {level1}_{level2}_{level3} requirements\n{level1}_{level2}_{level3}_package==1.0.0\ncommon==1.0.0\n"
                )

    return str(base)


@pytest.fixture
def fake_tmp_path(fs: FakeFilesystem) -> pathlib.Path:
    """A fake temporary path for tests that need tmp_path with pyfakefs.

    Use this instead of pytest's tmp_path when the test also uses pyfakefs fixtures.
    """
    tmp = pathlib.Path("/fake/tmp")
    tmp.mkdir(parents=True, exist_ok=True)
    return tmp
