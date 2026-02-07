"""Package name validation and matching utilities."""

import re

import click
from packaging.specifiers import InvalidSpecifier, SpecifierSet


def validate_version_specifier(version_specifier: str) -> str:
    """Validate and normalize a version specifier.

    If no operator is provided, defaults to '=='.

    Args:
        version_specifier: Version string (e.g., "1.0.0", ">=2.0", "~=3.0")

    Returns:
        Normalized version specifier with operator.

    Raises:
        click.ClickException: If the version specifier is invalid.
    """
    if not version_specifier.startswith(("==", "!=", ">=", "<=", ">", "<", "~=")):
        version_specifier = f"=={version_specifier}"

    try:
        SpecifierSet(version_specifier)
        return version_specifier
    except InvalidSpecifier as e:
        raise click.ClickException(
            f"Invalid version specifier '{version_specifier}': {e}"
        ) from e


def check_package_name(package_name: str, line: str) -> bool:
    """Determine if a line contains the given package name.

    Handles various requirement formats:
    - Simple packages: requests, django
    - Versioned packages: requests==2.28.0, django>=4.0
    - Packages with extras: requests[security], django[argon2]
    - Local paths: ./local_package, ../shared
    - URL requirements: git+https://..., package @ https://...

    Args:
        package_name: The package name to search for.
        line: A line from a requirements.txt file.

    Returns:
        True if the line contains the package, False otherwise.
    """
    package_name_lower = package_name.lower()
    line_lower = line.lower().strip()

    if package_name_lower == line_lower:
        return True

    if line.strip().startswith("#"):
        return False

    if _is_url_requirement(line):
        url_package = _extract_package_from_url(line)
        if url_package:
            url_package_normalized = url_package.replace("-", "_")
            package_normalized = package_name_lower.replace("-", "_")
            return url_package_normalized == package_normalized
        return False

    if "-" in package_name_lower:
        line_lower = line_lower.replace("_", "-")
    if "_" in package_name_lower:
        line_lower = line_lower.replace("-", "_")

    if line_lower.startswith(("./", "../")):
        return package_name_lower in line_lower.split("/")[-1]

    line_lower = re.split(r"\[", line_lower)[0]
    line_lower = re.split(r"~=|==|>=|<=|!=|>|<", line_lower)[0].strip()

    return package_name_lower == line_lower


def _is_url_requirement(line: str) -> bool:
    """Check if a line is a URL-based requirement.

    Handles:
    - VCS URLs: git+https://..., hg+https://..., svn+..., bzr+...
    - Direct URLs: http://..., https://..., file://...
    - PEP 440 URL syntax: package @ https://...
    """
    line_stripped = line.strip().lower()
    url_prefixes = (
        "git+",
        "git://",
        "hg+",
        "svn+",
        "bzr+",
        "http://",
        "https://",
        "file://",
    )
    if line_stripped.startswith(url_prefixes):
        return True

    return " @ " in line_stripped


def _extract_package_from_url(line: str) -> str | None:
    """Extract package name from a URL-based requirement.

    Handles formats like:
    - git+https://github.com/user/repo.git#egg=package_name
    - git+https://github.com/user/repo.git@v1.0#egg=package_name
    - package @ https://example.com/package.whl
    """
    line_stripped = line.strip()

    if "#egg=" in line_stripped.lower():
        egg_part = line_stripped.lower().split("#egg=")[-1]
        return egg_part.split("&")[0].split("#")[0].strip()

    if " @ " in line_stripped:
        return line_stripped.split(" @ ")[0].strip().lower()

    if "github.com" in line_stripped or "gitlab.com" in line_stripped:
        match = re.search(r"/([^/]+?)(?:\.git)?(?:@|#|$)", line_stripped)
        if match:
            return match.group(1).lower()

    return None
