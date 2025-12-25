import tomllib
from pathlib import Path

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


def get_test_dependencies() -> list[str]:
    """Read pytest-related dev dependencies from pyproject.toml."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    dev_deps = pyproject.get("dependency-groups", {}).get("dev", [])
    # Filter to only pytest-related dependencies for testing
    return [dep for dep in dev_deps if "pytest" in dep.lower()]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite across Python versions."""
    session.install(".", *get_test_dependencies())
    session.run("pytest", *session.posargs)
