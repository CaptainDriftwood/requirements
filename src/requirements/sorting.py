"""Sorting utilities for requirements.txt files."""

import re


def sort_packages(lines: list[str]) -> list[str]:
    """Sort package lines from a requirements.txt file.

    Implements Option A sorting:
    - Filters out standalone comment lines (lines starting with #)
    - Separates path references from regular packages
    - Sorts regular packages alphabetically (C locale / ASCII order)
    - Appends path references at the end (preserving original order)
    - Preserves inline comments on package lines

    Args:
        lines: List of lines from a requirements.txt file

    Returns:
        Sorted list of package lines (comments removed, path refs at end)
    """
    if not lines:
        return lines

    regular_packages: list[str] = []
    path_references: list[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if _is_path_reference(stripped):
            path_references.append(line)
        else:
            regular_packages.append(line)

    sorted_packages = sorted(regular_packages, key=_get_sort_key)

    return sorted_packages + path_references


def _is_path_reference(line: str) -> bool:
    """Check if a line is a path-based requirement.

    Detects:
    - Relative paths: ./package, ../package
    - Editable installs: -e ./package, -e ../package
    """
    stripped = line.strip().lower()

    if stripped.startswith(("-e ./", "-e ../", "./", "../")):
        return True

    return stripped.startswith("-e ") and "/" in stripped


def _get_sort_key(line: str) -> str:
    """Extract the package name from a line for sorting purposes.

    Handles version specifiers and extras notation.
    Returns the raw package name (no lowercasing) to match C locale behavior.
    """
    stripped = line.strip()

    if "#" in stripped:
        stripped = stripped.split("#")[0].strip()

    stripped = re.split(r"\[", stripped)[0]

    return re.split(r"~=|==|>=|<=|!=|>|<", stripped)[0].strip()
