"""Tests for URL handling functions in requirements parsing."""

import pytest

from src.main import _extract_package_from_url, _is_url_requirement, check_package_name

# =============================================================================
# Tests for _is_url_requirement
# =============================================================================


@pytest.mark.parametrize(
    "line,expected",
    [
        # VCS URLs
        ("git+https://github.com/user/repo.git", True),
        ("git+ssh://git@github.com/user/repo.git", True),
        ("git://github.com/user/repo.git", True),
        ("hg+https://bitbucket.org/user/repo", True),
        ("svn+https://svn.example.com/repo", True),
        ("bzr+https://launchpad.net/project", True),
        # Direct URLs
        ("https://example.com/package.whl", True),
        ("http://example.com/package.tar.gz", True),
        ("file:///local/path/to/package.whl", True),
        # With egg fragments
        ("git+https://github.com/user/repo.git#egg=mypackage", True),
        ("git+https://github.com/user/repo.git@v1.0#egg=mypackage", True),
        # Case insensitivity
        ("GIT+HTTPS://github.com/user/repo.git", True),
        ("HTTPS://example.com/package.whl", True),
        # PEP 440 URL syntax (package @ URL)
        ("mypackage @ https://example.com/package.whl", True),
        ("my-package @ https://files.pythonhosted.org/package.tar.gz", True),
        ("package_name @ file:///local/path/package.whl", True),
        ("Django @ https://example.com/Django-4.0.whl", True),
        # Non-URL requirements
        ("requests", False),
        ("requests==2.28.0", False),
        ("django>=4.0", False),
        ("./local_package", False),
        ("../shared_lib", False),
        ("", False),
        ("   ", False),
    ],
)
def test_is_url_requirement(line: str, expected: bool) -> None:
    """Test URL detection for various input formats."""
    assert _is_url_requirement(line) == expected


# =============================================================================
# Tests for _extract_package_from_url
# =============================================================================


@pytest.mark.parametrize(
    "line,expected",
    [
        # Egg fragment extraction
        ("git+https://github.com/user/repo.git#egg=mypackage", "mypackage"),
        ("git+https://github.com/user/repo.git@v1.0#egg=mypackage", "mypackage"),
        ("git+https://github.com/user/repo.git@main#egg=my_package", "my_package"),
        ("git+https://github.com/user/repo#egg=Package-Name", "package-name"),
        # Egg with additional fragments
        (
            "git+https://github.com/user/repo.git#egg=mypackage&subdirectory=src",
            "mypackage",
        ),
        # PEP 440 URL syntax (package @ URL)
        ("mypackage @ https://example.com/mypackage-1.0.whl", "mypackage"),
        ("My-Package @ https://example.com/package.tar.gz", "my-package"),
        ("package_name @ file:///local/path.whl", "package_name"),
        # GitHub/GitLab repo name extraction (fallback)
        ("git+https://github.com/user/myrepo.git", "myrepo"),
        ("git+https://github.com/user/my-repo.git", "my-repo"),
        ("git+https://gitlab.com/user/myrepo.git", "myrepo"),
        ("git+https://github.com/user/repo@v1.0", "repo"),
        ("git+https://github.com/user/repo.git@main", "repo"),
        # No extractable package name
        ("https://example.com/package.whl", None),
        ("http://random-server.com/file.tar.gz", None),
        ("file:///local/path/package.whl", None),
    ],
)
def test_extract_package_from_url(line: str, expected: str | None) -> None:
    """Test package name extraction from various URL formats."""
    assert _extract_package_from_url(line) == expected


def test_extract_preserves_lowercase_for_comparison() -> None:
    """Test that extracted names are lowercase for consistent comparison."""
    result = _extract_package_from_url(
        "git+https://github.com/user/repo.git#egg=MyPackage"
    )
    assert result == "mypackage"

    result = _extract_package_from_url("MyPackage @ https://example.com/package.whl")
    assert result == "mypackage"


# =============================================================================
# Tests for check_package_name with URL-based requirements
# =============================================================================


@pytest.mark.parametrize(
    "package_name,line,expected",
    [
        # Egg fragment matching
        ("mypackage", "git+https://github.com/user/repo.git#egg=mypackage", True),
        ("mypackage", "git+https://github.com/user/repo.git@v1.0#egg=mypackage", True),
        # Case insensitivity
        ("MyPackage", "git+https://github.com/user/repo.git#egg=mypackage", True),
        ("mypackage", "git+https://github.com/user/repo.git#egg=MyPackage", True),
        # Dash/underscore normalization
        ("my-package", "git+https://github.com/user/repo.git#egg=my_package", True),
        ("my_package", "git+https://github.com/user/repo.git#egg=my-package", True),
        # PEP 440 URL syntax
        ("mypackage", "mypackage @ https://example.com/package.whl", True),
        ("my-package", "my_package @ https://example.com/package.whl", True),
        # GitHub repo name fallback
        ("myrepo", "git+https://github.com/user/myrepo.git", True),
        ("my-repo", "git+https://github.com/user/my-repo.git", True),
        # Non-matching
        ("otherpackage", "git+https://github.com/user/repo.git#egg=mypackage", False),
        ("different", "mypackage @ https://example.com/package.whl", False),
        # URL without extractable name returns False
        ("requests", "https://example.com/requests.whl", False),
    ],
)
def test_check_package_name_with_urls(
    package_name: str, line: str, expected: bool
) -> None:
    """Test package name matching with URL-based requirements."""
    assert check_package_name(package_name, line) == expected
