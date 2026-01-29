"""File discovery and path utilities for requirements.txt files."""

import os
import pathlib
import re

import click


def gather_requirements_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """Find all requirements.txt files in the given paths.

    Recursively searches directories for requirements.txt files while applying
    intelligent filtering to exclude virtual environments and build artifacts.

    Features:
        - Recursively searches directories using glob patterns
        - Excludes virtual environments: .venv, venv, virtualenv, .aws-sam
        - Skips symlinks to prevent infinite loops and unexpected behavior
        - Validates files still exist after discovery (handles race conditions)

    Args:
        paths: List of files or directories to search.

    Returns:
        List of valid requirements.txt file paths.
    """
    requirements_files = []

    for path in paths:
        if not path.exists():
            click.echo(f"Error: Path '{path}' does not exist", err=True)
            continue

        if path.is_file():
            if path.name == "requirements.txt":
                requirements_files.append(path)
            else:
                click.echo(
                    f"Error: '{path}' is not a requirements.txt file (found: {path.name})",
                    err=True,
                )
        elif path.is_dir():
            found_files = []
            for f in pathlib.Path(path).glob("**/requirements.txt"):
                if not f.is_symlink():
                    found_files.append(f)
            if not found_files:
                click.echo(
                    f"Warning: No requirements.txt files found in directory '{path}'",
                    err=True,
                )
            requirements_files.extend(found_files)
        else:
            click.echo(f"Error: '{path}' is neither a file nor a directory", err=True)

    exclusion_pattern = re.compile(r"[/\\](venv|\.venv|virtualenv|\.aws-sam)[/\\]")
    validated_files = []

    for file in requirements_files:
        if exclusion_pattern.search(str(file)):
            continue

        if not file.exists():
            click.echo(f"Warning: File '{file}' no longer exists", err=True)
            continue

        validated_files.append(file)

    return validated_files


def resolve_paths(paths: tuple[str, ...]) -> list[pathlib.Path]:
    """Resolve the given paths into a list of pathlib.Path objects.

    Args:
        paths: Tuple of path strings from CLI arguments.

    Returns:
        List of Path objects. Returns current directory if no paths provided.
    """
    if not paths or (len(paths) == 1 and paths[0].strip() == "*"):
        return [pathlib.Path.cwd()]

    resolved_paths: list[pathlib.Path] = []
    for path in paths:
        resolved_paths.append(pathlib.Path(path.strip()))

    return resolved_paths


def check_file_writable(file_path: pathlib.Path, preview: bool = False) -> bool:
    """Check if a file is writable and warn user if not.

    Args:
        file_path: Path to the file to check.
        preview: If True, always returns True (no modification will happen).

    Returns:
        True if file is writable (or preview mode), False otherwise.
    """
    if preview:
        return True

    if not os.access(file_path, os.W_OK):
        click.echo(
            f"Warning: {file_path} is read-only, skipping file modification", err=True
        )
        return False

    return True
