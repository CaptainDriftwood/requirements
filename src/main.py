import locale
import logging
import os
import pathlib
import re
from collections.abc import Generator
from contextlib import contextmanager
from functools import cmp_to_key
from typing import Callable, Optional

import click
from packaging.specifiers import InvalidSpecifier, SpecifierSet

DEFAULT_LOCALE = "en_US.UTF-8"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


@contextmanager
def set_locale(new_locale: Optional[str] = None) -> Generator[Callable, None, None]:
    """Context manager to set the locale"""

    current_locale = locale.getlocale(locale.LC_COLLATE)
    try:
        locale.setlocale(locale.LC_COLLATE, new_locale)
        yield locale.strcoll
    finally:
        locale.setlocale(locale.LC_COLLATE, current_locale)


def sort_packages(
    packages: list[str], locale_: Optional[str] = None, preserve_comments: bool = True
) -> list[str]:
    """Sort a list of packages using specified locale with optional comment preservation"""

    if not preserve_comments:
        # Use the original simple sorting behavior
        if locale_ is None:
            return sorted(packages)
        try:
            with set_locale(locale_) as strcoll:
                return sorted(packages, key=cmp_to_key(strcoll))
        except locale.Error as e:
            logger.warning(
                f"Locale error encountered with locale '{locale_}': {e}. Falling back to default sorting."
            )
            return sorted(packages)

    # Smart sorting that preserves comment associations
    return _sort_with_comment_preservation(packages, locale_)


def _sort_with_comment_preservation(
    lines: list[str], locale_: Optional[str] = None
) -> list[str]:
    """Sort lines while preserving comment associations and file structure"""

    if not lines:
        return lines

    # Parse lines into sections and package groups
    sections = _parse_into_sections(lines)

    # Sort packages within each section while preserving comments
    sorted_sections = []
    for section in sections:
        sorted_sections.append(_sort_section(section, locale_))

    # Rebuild the file
    result = []
    for i, section in enumerate(sorted_sections):
        result.extend(section)
        # Add blank line between sections (except after the last section)
        if i < len(sorted_sections) - 1:
            result.append("")

    return result


def _parse_into_sections(lines: list[str]) -> list[list[str]]:
    """Parse lines into logical sections separated by blank lines"""

    sections = []
    current_section: list[str] = []

    for line in lines:
        if line.strip() == "":
            # Empty line - end current section if it has content
            if current_section:
                sections.append(current_section)
                current_section = []
        else:
            current_section.append(line)

    # Add the last section if it has content
    if current_section:
        sections.append(current_section)

    return sections


def _sort_section(section: list[str], locale_: Optional[str] = None) -> list[str]:
    """Sort packages within a section while keeping comments at the top"""

    if not section:
        return section

    # Separate comments from packages
    comments = []
    packages = []

    for line in section:
        stripped = line.strip()
        if stripped.startswith("#"):
            comments.append(line)
        elif stripped:  # Non-empty, non-comment line
            packages.append(line)

    # Sort packages
    def get_sort_key(line: str) -> str:
        # Extract package name for sorting
        package_name = (
            line.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split(">")[0]
            .split("<")[0]
            .split("!=")[0]
            .split("~=")[0]
            .strip()
        )
        return package_name.lower()

    if locale_ is None:
        sorted_packages = sorted(packages, key=get_sort_key)
    else:
        try:
            with set_locale(locale_) as strcoll:
                sorted_packages = sorted(
                    packages, key=lambda p: cmp_to_key(strcoll)(get_sort_key(p))
                )
        except locale.Error as e:
            logger.warning(
                f"Locale error encountered with locale '{locale_}': {e}. Falling back to default sorting."
            )
            sorted_packages = sorted(packages, key=get_sort_key)

    # Combine comments (in original order) + sorted packages
    return comments + sorted_packages


def gather_requirements_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """
    Find all requirements.txt files in the given paths, ignoring virtual environment/aws-sam
    related directories
    """
    requirements_files = []

    for path in paths:
        # First check if the path exists
        if not path.exists():
            click.echo(f"Error: Path '{path}' does not exist", err=True)
            continue

        # Check if it's a requirements.txt file
        if path.is_file():
            if path.name == "requirements.txt":
                requirements_files.append(path)
            else:
                click.echo(
                    f"Error: '{path}' is not a requirements.txt file (found: {path.name})",
                    err=True,
                )
        # Check if it's a directory
        elif path.is_dir():
            found_files = list(pathlib.Path(path).glob("**/requirements.txt"))
            if not found_files:
                click.echo(
                    f"Warning: No requirements.txt files found in directory '{path}'",
                    err=True,
                )
            requirements_files.extend(found_files)
        else:
            # This shouldn't happen if path.exists() is True, but handle edge cases
            click.echo(f"Error: '{path}' is neither a file nor a directory", err=True)

    # Filter out virtual environment directories and validate files still exist
    # Updated pattern to match only directory separators, not anywhere in the path
    exclusion_pattern = re.compile(r"[/\\](venv|\.venv|virtualenv|\.aws-sam)[/\\]")
    validated_files = []

    for file in requirements_files:
        if exclusion_pattern.search(str(file)):
            continue

        # Double-check file still exists (could have been deleted between glob and now)
        if not file.exists():
            click.echo(f"Warning: File '{file}' no longer exists", err=True)
            continue

        validated_files.append(file)

    return validated_files


def resolve_paths(paths: tuple[str, ...]) -> list[pathlib.Path]:
    """Resolve the given paths into a list of pathlib.Path objects"""

    if not paths or (len(paths) == 1 and paths[0].strip() == "*"):
        return [pathlib.Path.cwd()]

    resolved_paths: list[pathlib.Path] = []
    for path in paths:
        resolved_paths.append(pathlib.Path(path.strip()))

    return resolved_paths


def check_file_writable(file_path: pathlib.Path, preview: bool = False) -> bool:
    """Check if a file is writable and warn user if not (unless in preview mode)"""

    if preview:
        return True

    if not os.access(file_path, os.W_OK):
        click.echo(
            f"Warning: {file_path} is read-only, skipping file modification", err=True
        )
        return False

    return True


def validate_version_specifier(version_specifier: str) -> str:
    """Validate and normalize a version specifier"""
    # If the version specifier does not start with ==, !=, >=, <=, >, <, or ~=,
    # default to ==.
    if not version_specifier.startswith(("==", "!=", ">=", "<=", ">", "<", "~=")):
        version_specifier = f"=={version_specifier}"

    try:
        # Use packaging library to validate the version specifier
        SpecifierSet(version_specifier)
        return version_specifier
    except InvalidSpecifier as e:
        raise click.ClickException(
            f"Invalid version specifier '{version_specifier}': {e}"
        ) from e


def check_package_name(package_name: str, line: str) -> bool:
    """Determine if a line in a requirements.txt file contains the given package name"""

    # Convert to lowercase for case-insensitive comparison (pip is case-insensitive)
    package_name_lower = package_name.lower()
    line_lower = line.lower()

    if package_name_lower == line_lower:
        return True

    # If line is commented out, ignore it.
    if line.startswith("#"):
        return False

    # We make the package name and the line match in terms of dashes and underscores.
    if "-" in package_name_lower:
        line_lower = line_lower.replace("_", "-")
    if "_" in package_name_lower:
        line_lower = line_lower.replace("-", "_")

    # If the line is a package that is being referenced by a local path, we need to
    # check the last part of the path to see if it matches the package name.
    if line_lower.startswith(("./", "../")):
        return package_name_lower in line_lower.split("/")[-1]

    # Finally, we remove any sort of version specifier from the line and then check
    # if the package name matches.
    line_lower = re.split(r"~=|==|>=|<=|>|<|!=", line_lower)[0].strip()

    return package_name_lower == line_lower


@click.group(
    help="Manage requirements.txt files such as adding, removing, and updating individual packages in bulk"
)
@click.version_option(package_name="requirements")
def cli() -> None:
    pass


@cli.command(name="update")
@click.argument("package_name")
@click.argument("version_specifier")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def update_package(
    package_name: str,
    version_specifier: str,
    paths: tuple[str],
    preview: bool,
) -> None:
    """Update a package version in requirements.txt files.

    Updates the specified package to a new version across one or more requirements.txt files.
    Supports all PEP 440 version specifiers and automatically sorts the file after updates.

    \b
    Examples:
    Basic version update:
        requirements update django 4.2.0
        requirements update requests 2.28.0

    Version specifiers with operators:
        requirements update django ">=4.2.0"
        requirements update django "~=4.2.0"
        requirements update django "!=4.1.0"

    Complex version constraints:
        requirements update django ">=4.0.0,<5.0.0"
        requirements update requests ">=2.25.0,!=2.26.0"

    Preview changes without saving:
        requirements update django 4.2.0 --preview

    Target specific files or directories:
        requirements update django 4.2.0 /path/to/requirements.txt
        requirements update django 4.2.0 /project/backend /project/frontend
        requirements update django 4.2.0 /project  # Updates all requirements.txt in directory

    Multiple file paths:
        requirements update django 4.2.0 ./requirements.txt ./dev-requirements.txt

    \b
    Args:
    package_name: Name of the package to update (case-insensitive).
    version_specifier: Version specification (e.g., "4.2.0", ">=4.0.0", "~=4.2.0").
    paths: Optional paths to requirements files or directories. Defaults to current directory.
    preview: If True, shows changes without saving files.

    \b
    Note:
    - If no operator is provided, "==" is assumed (e.g., "4.2.0" becomes "==4.2.0")
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Files are automatically sorted after updates while preserving comments
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    """

    # Validate and normalize the version specifier
    version_specifier = validate_version_specifier(version_specifier)

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        modified = False

        for index, line in enumerate(contents):
            if check_package_name(package_name, line):
                # Preserve inline comments when updating
                inline_comment = ""
                if "#" in line and not line.strip().startswith("#"):
                    # Find the comment part and preserve it
                    comment_index = line.find("#")
                    inline_comment = "  " + line[comment_index:]

                contents[index] = f"{package_name}{version_specifier}{inline_comment}"
                modified = True
                contents = sort_packages(contents, locale_=DEFAULT_LOCALE)

        if modified:
            if preview:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(contents).strip() + "\n")
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(contents).strip() + "\n", encoding="utf-8"
                )
                click.echo(f"Updated {requirements_file}")


@cli.command(name="find")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print the package contained in the requirements.txt file",
)
def find_package(package_name: str, paths: tuple[str], verbose: bool) -> None:
    """Find a package in requirements.txt files.

    Searches for the specified package across requirements.txt files and reports
    which files contain it. Useful for locating package dependencies in large projects.

    \b
    Examples:
    Basic package search:
        requirements find django
        requirements find requests

    Verbose output (shows the exact line):
        requirements find django --verbose
        requirements find requests --verbose

    Search in specific files:
        requirements find django /path/to/requirements.txt
        requirements find django ./requirements.txt ./dev-requirements.txt

    Search in directories:
        requirements find django /project/backend
        requirements find django /project  # Searches all requirements.txt in directory

    Search in multiple locations:
        requirements find django /backend /frontend /shared

    \b
    Args:
    package_name: Name of the package to find (case-insensitive).
    paths: Optional paths to requirements files or directories. Defaults to current directory.
    verbose: If True, shows the exact line containing the package.

    \b
    Note:
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Ignores commented lines (lines starting with #)
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - Works with packages that have version specifiers, extras, or URLs
    """
    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        for line in requirements_file.read_text(encoding="utf-8").splitlines():
            if check_package_name(package_name, line):
                click.echo(requirements_file)
                if verbose:
                    click.echo(line)


@cli.command(name="add")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def add_package(package_name: str, paths: tuple[str], preview: bool) -> None:
    """Add a package to requirements.txt files.

    Adds the specified package to one or more requirements.txt files if it doesn't
    already exist. The package is added without a version specifier, and the file
    is automatically sorted after the addition.

    \b
    Examples:
    Basic package addition:
        requirements add requests
        requirements add django

    Preview changes without saving:
        requirements add requests --preview

    Add to specific files:
        requirements add requests /path/to/requirements.txt
        requirements add requests ./requirements.txt ./dev-requirements.txt

    Add to directories:
        requirements add requests /project/backend
        requirements add requests /project  # Adds to all requirements.txt in directory

    Add to multiple locations:
        requirements add requests /backend /frontend /shared

    \b
    Args:
    package_name: Name of the package to add.
    paths: Optional paths to requirements files or directories. Defaults to current directory.
    preview: If True, shows changes without saving files.

    \b
    Note:
    - Package is added without version specifier (no "==1.0.0" suffix)
    - If package already exists, a message is displayed and no changes are made
    - Package names are checked case-insensitively (won't add Django if django exists)
    - Files are automatically sorted after addition while preserving comments
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - Use 'requirements update' command to add packages with specific versions
    """

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        modified = False

        for line in contents:
            if check_package_name(package_name, line):
                click.echo(f"{package_name} already exists in {requirements_file}")
                break
        else:
            contents.append(package_name)
            contents = sort_packages(contents, locale_=DEFAULT_LOCALE)
            modified = True

        if modified:
            if preview:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(contents).strip() + "\n")
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(contents).strip() + "\n", encoding="utf-8"
                )
                click.echo(f"Updated {requirements_file}")


@cli.command(name="remove")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def remove_package(package_name: str, paths: tuple[str], preview: bool) -> None:
    """Remove a package from requirements.txt files.

    Removes the specified package from one or more requirements.txt files if it exists.
    The file is automatically sorted after removal while preserving comments and structure.

    \b
    Examples:
    Basic package removal:
        requirements remove requests
        requirements remove django

    Preview changes without saving:
        requirements remove requests --preview

    Remove from specific files:
        requirements remove requests /path/to/requirements.txt
        requirements remove requests ./requirements.txt ./dev-requirements.txt

    Remove from directories:
        requirements remove requests /project/backend
        requirements remove requests /project  # Removes from all requirements.txt in directory

    Remove from multiple locations:
        requirements remove requests /backend /frontend /shared

    \b
    Args:
    package_name: Name of the package to remove (case-insensitive).
    paths: Optional paths to requirements files or directories. Defaults to current directory.
    preview: If True, shows changes without saving files.

    \b
    Note:
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Removes the entire line including version specifiers and inline comments
    - If package doesn't exist, no error is raised and no changes are made
    - Files are automatically sorted after removal while preserving comments
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - Works with packages that have version specifiers, extras, or URLs
    """

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        updated_contents = [
            line for line in contents if not check_package_name(package_name, line)
        ]
        updated_contents = sort_packages(updated_contents, locale_=DEFAULT_LOCALE)

        if preview:
            click.echo(click.style(requirements_file, fg="cyan", bold=True))
            click.echo("\n".join(updated_contents).strip() + "\n")

        if (
            len(contents) != len(updated_contents)
            and not preview
            and check_file_writable(requirements_file, preview)
        ):
            requirements_file.write_text(
                "\n".join(updated_contents).strip() + "\n", encoding="utf-8"
            )
            click.echo(f"Removed {package_name} from {requirements_file}")


@cli.command(name="sort")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def sort_requirements(paths: tuple[str], preview: bool) -> None:
    """Sort requirements.txt files alphabetically.

    Sorts package entries in requirements.txt files while intelligently preserving
    comments and file structure. Comments stay associated with their sections,
    and blank lines separate logical sections.

    \b
    Examples:
    Sort current directory:
        requirements sort

    Preview changes without saving:
        requirements sort --preview

    Sort specific files:
        requirements sort /path/to/requirements.txt
        requirements sort ./requirements.txt ./dev-requirements.txt

    Sort directories:
        requirements sort /project/backend
        requirements sort /project  # Sorts all requirements.txt in directory

    Sort multiple locations:
        requirements sort /backend /frontend /shared

    \b
    Args:
    paths: Optional paths to requirements files or directories. Defaults to current directory.
    preview: If True, shows changes without saving files.

    \b
    Note:
    - Preserves comments and their association with nearby packages
    - Maintains blank lines that separate logical sections
    - Sorts packages alphabetically within each section
    - Comments at the top of sections stay at the top
    - Inline comments (after package names) are preserved
    - Uses locale-aware sorting with UTF-8 encoding
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - If file is already sorted, displays confirmation message
    """

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        new_contents = sort_packages(contents, locale_=DEFAULT_LOCALE)
        if contents != new_contents:
            if not preview:
                if check_file_writable(requirements_file, preview):
                    requirements_file.write_text(
                        "\n".join(new_contents).strip() + "\n", encoding="utf-8"
                    )
                    click.echo(f"Sorted {requirements_file}")
            else:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(new_contents).strip() + "\n")
        else:
            click.echo(f"{requirements_file} is already sorted")


@cli.command(name="cat")
@click.argument("paths", nargs=-1)
def cat_requirements(paths: tuple[str]) -> None:
    """Display the contents of requirements.txt files.

    Shows the content of one or more requirements.txt files with clear file headers.
    Useful for quickly viewing dependencies across multiple files or projects.

    \b
    Examples:
    Display current directory files:
        requirements cat

    Display specific files:
        requirements cat /path/to/requirements.txt
        requirements cat ./requirements.txt ./dev-requirements.txt

    Display files in directories:
        requirements cat /project/backend
        requirements cat /project  # Shows all requirements.txt in directory

    Display files in multiple locations:
        requirements cat /backend /frontend /shared

    \b
    Args:
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Each file is displayed with a colored header showing the file path
    - Multiple files are separated by blank lines for readability
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - Shows files exactly as they exist (no sorting or modification)
    - If no requirements.txt files are found, no output is produced
    - Useful for debugging dependency issues across multiple files
    """

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        click.echo(click.style(requirements_file, fg="cyan", bold=True))
        click.echo(requirements_file.read_text(encoding="utf-8").strip())
        click.echo()


if __name__ == "__main__":
    cli()
