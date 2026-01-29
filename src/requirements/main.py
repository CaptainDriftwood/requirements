"""CLI for managing requirements.txt files."""

from __future__ import annotations

import difflib
import urllib.error
from typing import TYPE_CHECKING, Final

import click

from requirements.config import (
    ensure_config_dir,
    get_config_file,
    get_default_config_content,
    load_config,
    save_color_setting,
)
from requirements.console import create_console
from requirements.files import (
    check_file_writable,
    gather_requirements_files,
    resolve_paths,
)
from requirements.packages import check_package_name, validate_version_specifier
from requirements.pypi import fetch_package_versions
from requirements.sorting import sort_packages

if TYPE_CHECKING:
    from rich.console import Console

# Key for storing console in click context
CONSOLE_KEY: Final[str] = "console"


def get_console_from_context(ctx: click.Context) -> Console:
    """Get the console from click context, creating one if needed.

    This handles the case where a subcommand is invoked directly in tests
    without going through the main CLI group.

    Args:
        ctx: Click context object.

    Returns:
        Console instance from context or a new default console.
    """
    if ctx.obj is None:
        ctx.obj = {}
    if CONSOLE_KEY not in ctx.obj:
        ctx.obj[CONSOLE_KEY] = create_console()
    return ctx.obj[CONSOLE_KEY]


def print_unified_diff(
    console: Console,
    old_lines: list[str],
    new_lines: list[str],
) -> None:
    """Print unified diff output showing all lines with changes marked.

    Displays the full file content with changed lines prefixed by +/- markers
    and unchanged lines prefixed with a space for alignment.

    Args:
        console: Rich console instance for output.
        old_lines: Original file lines.
        new_lines: Modified file lines.
    """
    diff = difflib.unified_diff(
        old_lines, new_lines, lineterm="", n=max(len(old_lines), len(new_lines))
    )
    for line in diff:
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("-"):
            console.print(f"[diff.removed]{line}[/diff.removed]")
        elif line.startswith("+"):
            console.print(f"[diff.added]{line}[/diff.added]")
        else:
            console.print(line)
    console.print()


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

\b
Color Output:
    Color output is enabled by default and auto-detected based on terminal support.
    Use --color/--no-color to override, or set the NO_COLOR environment variable.
"""
)
@click.option(
    "--color/--no-color",
    default=None,
    help="Enable or disable colored output. Auto-detected by default.",
)
@click.version_option(package_name="requirements")
@click.pass_context
def cli(ctx: click.Context, color: bool | None) -> None:
    """Main CLI entry point."""
    ctx.ensure_object(dict)
    ctx.obj[CONSOLE_KEY] = create_console(color)


@cli.command(name="update")
@click.argument("package_name")
@click.argument("version_specifier")
@click.argument("paths", nargs=-1)
@click.option(
    "--preview", "--dry-run", is_flag=True, help="Preview file changes without saving"
)
@click.pass_context
def update_package(
    ctx: click.Context,
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
    console = get_console_from_context(ctx)
    version_specifier = validate_version_specifier(version_specifier)

    if preview:
        console.print("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        original_contents = requirements_file.read_text(encoding="utf-8").splitlines()
        contents = original_contents.copy()
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
                console.print(str(requirements_file), style="path")
                print_unified_diff(console, original_contents, contents)
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(contents).strip() + "\n", encoding="utf-8"
                )
                console.print(f"Updated {requirements_file}")


@cli.command(name="find")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print the package contained in the requirements.txt file",
)
@click.pass_context
def find_package(
    ctx: click.Context, package_name: str, paths: tuple[str], verbose: bool
) -> None:
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
    console = get_console_from_context(ctx)
    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        for line in requirements_file.read_text(encoding="utf-8").splitlines():
            if check_package_name(package_name, line):
                console.print(str(requirements_file))
                if verbose:
                    console.print(line)


@cli.command(name="add")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option(
    "--preview", "--dry-run", is_flag=True, help="Preview file changes without saving"
)
@click.pass_context
def add_package(
    ctx: click.Context, package_name: str, paths: tuple[str], preview: bool
) -> None:
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
    console = get_console_from_context(ctx)
    if preview:
        console.print("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        original_contents = requirements_file.read_text(encoding="utf-8").splitlines()
        contents = original_contents.copy()
        modified = False

        for line in contents:
            if check_package_name(package_name, line):
                console.print(f"{package_name} already exists in {requirements_file}")
                break
        else:
            contents.append(package_name)
            contents = sort_packages(contents)
            modified = True

        if modified:
            if preview:
                console.print(str(requirements_file), style="path")
                print_unified_diff(console, original_contents, contents)
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(contents).strip() + "\n", encoding="utf-8"
                )
                console.print(f"Updated {requirements_file}")


@cli.command(name="remove")
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option(
    "--preview", "--dry-run", is_flag=True, help="Preview file changes without saving"
)
@click.pass_context
def remove_package(
    ctx: click.Context, package_name: str, paths: tuple[str], preview: bool
) -> None:
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
    console = get_console_from_context(ctx)
    if preview:
        console.print("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        original_contents = requirements_file.read_text(encoding="utf-8").splitlines()
        updated_contents = [
            line
            for line in original_contents
            if not check_package_name(package_name, line)
        ]
        updated_contents = sort_packages(updated_contents)

        if len(original_contents) != len(updated_contents):
            if preview:
                console.print(str(requirements_file), style="path")
                print_unified_diff(console, original_contents, updated_contents)
            elif check_file_writable(requirements_file, preview):
                requirements_file.write_text(
                    "\n".join(updated_contents).strip() + "\n", encoding="utf-8"
                )
                console.print(f"Removed {package_name} from {requirements_file}")


@cli.command(name="sort")
@click.argument("paths", nargs=-1)
@click.option(
    "--preview", "--dry-run", is_flag=True, help="Preview file changes without saving"
)
@click.pass_context
def sort_requirements(ctx: click.Context, paths: tuple[str], preview: bool) -> None:
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
    console = get_console_from_context(ctx)
    if preview:
        console.print("Previewing changes")

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
                    console.print(f"Sorted {requirements_file}")
                    files_sorted += 1
                else:
                    files_skipped += 1
            else:
                console.print(str(requirements_file), style="path")
                print_unified_diff(console, contents, new_contents)
                files_sorted += 1
        else:
            console.print(f"{requirements_file} is already sorted")
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
        console.print(
            f"\nSummary: {', '.join(summary_parts)} ({total_files} files total)"
        )


@cli.command(name="cat")
@click.argument("paths", nargs=-1)
@click.pass_context
def cat_requirements(ctx: click.Context, paths: tuple[str]) -> None:
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
    console = get_console_from_context(ctx)
    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        console.print(str(requirements_file), style="path")
        console.print(requirements_file.read_text(encoding="utf-8").strip())
        console.print()


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
@click.pass_context
def show_versions(
    ctx: click.Context,
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
    console = get_console_from_context(ctx)
    try:
        versions = fetch_package_versions(package_name, index_url)

        if not versions:
            raise click.ClickException(f"No versions found for '{package_name}'")

        latest = versions[0] if versions else None

        if latest:
            console.print(
                f"[package]{package_name}[/package] (latest: [version]{latest}[/version])"
            )
        else:
            console.print(f"[package]{package_name}[/package]")

        total_versions = len(versions)
        display_versions = versions if show_all else versions[:limit]

        if one_per_line:
            for version in display_versions:
                console.print(version)
        else:
            console.print(f"Available versions: {', '.join(display_versions)}")

            if not show_all and total_versions > limit:
                console.print(
                    f"(showing {limit} of {total_versions} versions, "
                    "use --all for complete list)",
                    style="warning",
                )

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise click.ClickException(f"Package '{package_name}' not found") from e
        raise click.ClickException(f"HTTP error: {e}") from e
    except urllib.error.URLError as e:
        raise click.ClickException(f"Network error: {e.reason}") from e


@cli.group(name="config")
def config_group() -> None:
    """Manage CLI configuration settings.

    Configuration is stored in ~/.requirements/config.toml.

    \b
    Examples:
    Show current configuration:
        requirements config show

    Enable colored output:
        requirements config set color true

    Disable colored output:
        requirements config set color false

    Show config file path:
        requirements config path
    """


@config_group.command(name="show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration settings."""
    console = get_console_from_context(ctx)
    config_file = get_config_file()
    config = load_config()

    console.print(f"[path]Config file:[/path] {config_file}")

    if not config:
        console.print("No configuration set (using defaults)")
        return

    console.print("\nCurrent settings:")
    for section, values in config.items():
        if isinstance(values, dict):
            for key, value in values.items():
                console.print(f"  {section}.{key} = {value}")
        else:
            console.print(f"  {section} = {values}")


@config_group.command(name="path")
@click.pass_context
def config_path(ctx: click.Context) -> None:
    """Show the configuration file path."""
    console = get_console_from_context(ctx)
    console.print(str(get_config_file()))


@config_group.command(name="set")
@click.argument("setting", type=click.Choice(["color"]))
@click.argument("value", type=click.Choice(["true", "false"]))
@click.pass_context
def config_set(ctx: click.Context, setting: str, value: str) -> None:
    """Set a configuration value.

    \b
    Available settings:
        color: Enable/disable colored output (true/false)
    """
    console = get_console_from_context(ctx)

    if setting == "color":
        enabled = value == "true"
        save_color_setting(enabled)
        status = "enabled" if enabled else "disabled"
        console.print(f"Color output {status}")


@config_group.command(name="init")
@click.pass_context
def config_init(ctx: click.Context) -> None:
    """Initialize configuration file with defaults.

    Creates ~/.requirements/config.toml with default settings if it doesn't exist.
    """
    console = get_console_from_context(ctx)
    config_file = get_config_file()

    if config_file.exists():
        console.print(f"Config file already exists: {config_file}")
        return

    ensure_config_dir()
    config_file.write_text(get_default_config_content())
    console.print(f"Created config file: {config_file}")


if __name__ == "__main__":
    cli()
