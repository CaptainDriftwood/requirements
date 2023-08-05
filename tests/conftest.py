import pathlib
import tempfile

import pytest


@pytest.fixture
def requirements_txt():
    return b"pytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n"


@pytest.fixture
def virtual_directory(requirements_txt):
    """Temporary directory with a single requirements.txt file in it"""

    with tempfile.TemporaryDirectory() as td:
        requirements_file = pathlib.Path(td) / "requirements.txt"
        requirements_file.write_text(requirements_txt.decode("utf-8"))
        yield td


@pytest.fixture
def single_requirements_file(requirements_txt):
    """Temporary requirements.txt file"""

    with tempfile.NamedTemporaryFile() as tf:
        tf.write(requirements_txt)
        tf.seek(0)
        yield tf.name


@pytest.fixture
def multiple_nested_directories(requirements_txt):
    """Multiple temporary nested directories with a single requirements.txt file in each"""

    with tempfile.TemporaryDirectory() as td:
        for i in range(3):
            directory = pathlib.Path(td) / f"directory{i}"
            directory.mkdir()
            requirements_file = directory / "requirements.txt"
            requirements_file.write_text(requirements_txt.decode("utf-8"))
        yield td
