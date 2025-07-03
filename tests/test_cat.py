from click.testing import CliRunner

from src.main import cat_requirements


def test_cat_requirements(cli_runner: CliRunner, single_requirements_file: str) -> None:
    result = cli_runner.invoke(cat_requirements, [single_requirements_file])
    assert result.exit_code == 0
    assert (
        result.output
        == f"{single_requirements_file}/requirements.txt\npytest\nboto3~=1.0.0\nenhancement-models==1.0.0\n\n"
    )
