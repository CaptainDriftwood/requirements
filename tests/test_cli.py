from click.testing import CliRunner
from requirements.main import cli


def test_single_requirements_file(single_requirements_file):
    runner = CliRunner()
    result = runner.invoke(
        cli, ["pytest", "pytest~=6.0.0", "tests/requirements.txt", "--preview"]
    )
    assert result.exit_code == 0
    assert "Previewing changes" in result.output


def test_multiple_requirements_files():
    pass


def test_single_directory():
    pass


def test_multiple_directories():
    pass
