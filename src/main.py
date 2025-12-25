"""CLI for managing requirements.txt files."""

import urllib.error

import click

from src.files import check_file_writable, gather_requirements_files, resolve_paths
from src.packages import check_package_name, validate_version_specifier
from src.pypi import fetch_package_versions
from src.sorting import sort_packages


@click.group(
    help="""Manage requirements.txt files such as adding, removing, and updating individual packages in bulk.

\b
Exit Codes:
    0: Success (operation completed, or no changes needed)
    1: Error (invalid arguments, file not found, or operation failed)

\b
Excluded Directories:
    The following directories are automatically excluded from searches:
    .venv, venv, virtualenv, .aws-sam
"""
)
@click.version_option(package_name="requirements")
def cli() -> None:
    """Main CLI entry point."""


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

    \b
    Args:
    package_name: Name of the package to update (case-insensitive).
    version_specifier: Version specification (e.g., "4.2.0", ">=4.0.0", "~=4.2.0").
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - If no operator is provided, "==" is assumed (e.g., "4.2.0" becomes "==4.2.0")
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Files are automatically sorted after updates
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    """
    version_specifier = validate_version_specifier(version_specifier)

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        modified = False

        for index, line in enumerate(contents):
            if check_package_name(package_name, line):
                inline_comment = ""
                if "#" in line and not line.strip().startswith("#"):
                    comment_index = line.find("#")
                    inline_comment = "  " + line[comment_index:]

                contents[index] = f"{package_name}{version_specifier}{inline_comment}"
                modified = True
                contents = sort_packages(contents)

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

    \b
    Args:
    package_name: Name of the package to find (case-insensitive).
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Ignores commented lines (lines starting with #)
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
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

    \b
    Args:
    package_name: Name of the package to add.
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Package is added without version specifier (no "==1.0.0" suffix)
    - If package already exists, a message is displayed and no changes are made
    - Package names are checked case-insensitively (won't add Django if django exists)
    - Files are automatically sorted after addition
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
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
            contents = sort_packages(contents)
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
    The file is automatically sorted after removal.

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

    \b
    Args:
    package_name: Name of the package to remove (case-insensitive).
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Package names are matched case-insensitively (Django, django, DJANGO all match)
    - Handles package name variations with hyphens/underscores automatically
    - Removes the entire line including version specifiers and inline comments
    - If package doesn't exist, no error is raised and no changes are made
    - Files are automatically sorted after removal
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    """
    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        updated_contents = [
            line for line in contents if not check_package_name(package_name, line)
        ]
        updated_contents = sort_packages(updated_contents)

        if len(contents) != len(updated_contents):
            if preview:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(updated_contents).strip() + "\n")
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(updated_contents).strip() + "\n", encoding="utf-8"
                )
                click.echo(f"Removed {package_name} from {requirements_file}")


@cli.command(name="sort")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def sort_requirements(paths: tuple[str], preview: bool) -> None:
    """Sort requirements.txt files alphabetically.

    Sorts package entries in requirements.txt files using C locale (ASCII) ordering.
    Comments are removed and path-based references are placed at the end.

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

    \b
    Args:
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Uses C locale (ASCII) ordering to match GNU sort behavior
    - Standalone comment lines are removed during sorting
    - Inline comments on package lines are preserved
    - Path references (./pkg, ../pkg, -e ./pkg) are placed at the end
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    """
    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)
    files_sorted = 0
    files_already_sorted = 0
    files_skipped = 0

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text(encoding="utf-8").splitlines()
        new_contents = sort_packages(contents)
        if contents != new_contents:
            if not preview:
                if check_file_writable(requirements_file, preview):
                    requirements_file.write_text(
                        "\n".join(new_contents).strip() + "\n", encoding="utf-8"
                    )
                    click.echo(f"Sorted {requirements_file}")
                    files_sorted += 1
                else:
                    files_skipped += 1
            else:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(new_contents).strip() + "\n")
                files_sorted += 1
        else:
            click.echo(f"{requirements_file} is already sorted")
            files_already_sorted += 1

    total_files = files_sorted + files_already_sorted + files_skipped
    if total_files > 1:
        summary_parts = []
        if files_sorted:
            summary_parts.append(f"{files_sorted} sorted")
        if files_already_sorted:
            summary_parts.append(f"{files_already_sorted} already sorted")
        if files_skipped:
            summary_parts.append(f"{files_skipped} skipped")
        click.echo(f"\nSummary: {', '.join(summary_parts)} ({total_files} files total)")


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

    \b
    Args:
    paths: Optional paths to requirements files or directories. Defaults to current directory.

    \b
    Note:
    - Each file is displayed with a colored header showing the file path
    - Multiple files are separated by blank lines for readability
    - Excludes virtual environment directories (.venv, venv, virtualenv, .aws-sam)
    - Shows files exactly as they exist (no sorting or modification)
    """
    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        click.echo(click.style(requirements_file, fg="cyan", bold=True))
        click.echo(requirements_file.read_text(encoding="utf-8").strip())
        click.echo()


@cli.command(name="versions")
@click.argument("package_name")
@click.option(
    "--all",
    "show_all",
    is_flag=True,
    help="Show all available versions (default: 10 most recent)",
)
@click.option(
    "--limit",
    default=10,
    type=int,
    help="Number of versions to show (default: 10)",
)
@click.option(
    "-1",
    "--one-per-line",
    "one_per_line",
    is_flag=True,
    help="Print each version on its own line (useful for piping)",
)
@click.option(
    "--index-url",
    help="Custom PyPI index URL (e.g., private Nexus repository)",
    metavar="URL",
)
def show_versions(
    package_name: str,
    show_all: bool,
    limit: int,
    one_per_line: bool,
    index_url: str | None,
) -> None:
    """Show available versions of a package from PyPI.

    Queries the package index (PyPI or a custom index) for available versions
    of the specified package. By default shows the 10 most recent versions.

    \b
    Examples:
    Show recent versions:
        requirements versions requests
        requirements versions django

    Show all versions:
        requirements versions requests --all

    Show specific number of versions:
        requirements versions django --limit 20

    Use with private index (Nexus, Artifactory, etc.):
        requirements versions mypackage --index-url https://nexus.example.com/repository/pypi/simple

    \b
    Args:
    package_name: Name of the package to query.

    \b
    Note:
    - Works with PyPI, Nexus, Artifactory, DevPI, and any PEP 503 compliant index
    - Uses the Simple API (PEP 503) to query package versions
    """
    try:
        versions = fetch_package_versions(package_name, index_url)

        if not versions:
            raise click.ClickException(f"No versions found for '{package_name}'")

        latest = versions[0] if versions else None

        if latest:
            click.echo(
                f"{click.style(package_name, fg='cyan', bold=True)} "
                f"(latest: {click.style(latest, fg='green')})"
            )
        else:
            click.echo(click.style(package_name, fg="cyan", bold=True))

        total_versions = len(versions)
        display_versions = versions if show_all else versions[:limit]

        if one_per_line:
            for version in display_versions:
                click.echo(version)
        else:
            click.echo(f"Available versions: {', '.join(display_versions)}")

            if not show_all and total_versions > limit:
                click.echo(
                    click.style(
                        f"(showing {limit} of {total_versions} versions, "
                        "use --all for complete list)",
                        fg="yellow",
                    )
                )

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise click.ClickException(f"Package '{package_name}' not found") from e
        raise click.ClickException(f"HTTP error: {e}") from e
    except urllib.error.URLError as e:
        raise click.ClickException(f"Network error: {e.reason}") from e


if __name__ == "__main__":
    cli()
