import pathlib

import pytest

from src.main import (
    check_package_name,
    gather_requirements_files,
    resolve_paths,
)


class TestGatherRequirementsFiles:
    """Test functionality when locating requirements.txt files"""

    def test_single_requirements_file(self, single_requirements_file: str) -> None:
        filepath = pathlib.Path(single_requirements_file)
        files = gather_requirements_files([filepath])
        assert len(files) == 1

    def test_multiple_requirements_files(
        self, multiple_nested_directories: str
    ) -> None:
        filepath = pathlib.Path(multiple_nested_directories)
        files = gather_requirements_files([filepath])
        assert len(files) == 4


class TestResolvePathsFunction:
    """Test resolve_paths function"""

    def test_resolve_single_path(self) -> None:
        """Test resolving a single path"""
        result = resolve_paths(("test_path",))
        assert len(result) == 1
        assert result[0] == pathlib.Path("test_path")

    def test_resolve_multiple_paths(self) -> None:
        """Test resolving multiple paths"""
        result = resolve_paths(("path1 path2 path3",))
        assert len(result) == 3
        assert result[0] == pathlib.Path("path1")
        assert result[1] == pathlib.Path("path2")
        assert result[2] == pathlib.Path("path3")

    def test_resolve_empty_paths(self) -> None:
        """Test resolving empty paths defaults to current directory"""
        result = resolve_paths(())
        assert len(result) == 1
        assert result[0] == pathlib.Path.cwd()

    def test_resolve_wildcard_path(self) -> None:
        """Test resolving wildcard path defaults to current directory"""
        result = resolve_paths(("*",))
        assert len(result) == 1
        assert result[0] == pathlib.Path.cwd()


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
def test_check_package_name(package_name: str, line: str, expected: bool) -> None:
    assert check_package_name(package_name, line) == expected
