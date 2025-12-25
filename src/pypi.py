"""PyPI Simple API client for querying package versions."""

import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

from packaging.version import InvalidVersion, Version

DEFAULT_INDEX_URL = "https://pypi.org/simple/"


class SimpleAPIParser(HTMLParser):
    """Parse PEP 503 Simple API HTML response to extract package versions."""

    def __init__(self) -> None:
        super().__init__()
        self.files: list[tuple[str, bool]] = []  # (filename, is_yanked)
        self._current_yanked = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._current_yanked = any(name == "data-yanked" for name, _ in attrs)

    def handle_data(self, data: str) -> None:
        data = data.strip()
        if data and data.endswith((".whl", ".tar.gz")):
            self.files.append((data, self._current_yanked))


def _extract_version_from_filename(filename: str, package_name: str) -> str | None:
    """Extract version from a package filename.

    Handles both wheel and sdist formats:
    - package_name-1.2.3-py3-none-any.whl
    - package_name-1.2.3.tar.gz
    """
    # Normalize package name for matching (PEP 503: replace [-_.] with -)
    # Then build a pattern that matches any separator variant
    normalized = re.sub(r"[-_.]+", "-", package_name.lower())
    # Split by separator and rejoin with pattern that matches any separator
    name_parts = normalized.split("-")
    name_pattern = "[-_.]+".join(re.escape(part) for part in name_parts)

    # Try wheel format: {name}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    wheel_match = re.match(
        rf"^{name_pattern}[-_](.+?)-(?:py|cp)\d",
        filename.lower(),
    )
    if wheel_match:
        return wheel_match.group(1)

    # Try sdist format: {name}-{version}.tar.gz
    sdist_match = re.match(
        rf"^{name_pattern}[-_](.+?)\.tar\.gz$",
        filename.lower(),
    )
    if sdist_match:
        return sdist_match.group(1)

    return None


def fetch_package_versions(
    package_name: str,
    index_url: str | None = None,
    include_yanked: bool = False,
) -> list[str]:
    """Fetch available versions for a package from a PEP 503 Simple API.

    Args:
        package_name: Name of the package to query.
        index_url: Base URL of the Simple API (default: PyPI).
        include_yanked: Whether to include yanked versions.

    Returns:
        List of version strings, sorted newest first.

    Raises:
        urllib.error.HTTPError: If the package is not found (404) or other HTTP error.
        urllib.error.URLError: If there's a network error.
    """
    if index_url is None:
        index_url = DEFAULT_INDEX_URL

    # Normalize package name for URL (PEP 503)
    normalized_name = re.sub(r"[-_.]+", "-", package_name.lower())

    # Ensure index_url ends with /
    if not index_url.endswith("/"):
        index_url += "/"

    url = f"{index_url}{normalized_name}/"

    request = urllib.request.Request(
        url,
        headers={"Accept": "text/html", "User-Agent": "requirements-cli"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    parser = SimpleAPIParser()
    parser.feed(html)

    # Extract versions from filenames
    versions_set: set[str] = set()
    for filename, is_yanked in parser.files:
        if is_yanked and not include_yanked:
            continue

        version_str = _extract_version_from_filename(filename, package_name)
        if version_str:
            # Validate it's a proper version
            try:
                Version(version_str)
                versions_set.add(version_str)
            except InvalidVersion:
                # Skip invalid versions (e.g., legacy formats)
                continue

    return sorted(versions_set, key=Version, reverse=True)
