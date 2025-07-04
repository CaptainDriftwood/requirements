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

DEFAULT_LOCALE = "en_US.UTF-8"

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


def sort_packages(packages: list[str], locale_: Optional[str] = None) -> list[str]:
    """Sort a list of packages using specified locale"""

    if locale_ is None:
        return sorted(packages)
    else:
        try:
            with set_locale(locale_) as strcoll:
                return sorted(packages, key=cmp_to_key(strcoll))
        except locale.Error as e:
            logging.warning(
                f"Locale error encountered with locale '{locale_}': {e}. Falling back to default sorting."
            )
            return sorted(packages)


def gather_requirements_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    """
    Find all requirements.txt files in the given paths, ignoring virtual environment/aws-sam
    related directories
    """
    requirements_files = []

    for path in paths:
        if path.is_file() and path.name == "requirements.txt":
            requirements_files.append(path)
        elif path.is_dir():
            requirements_files.extend(pathlib.Path(path).glob("**/requirements.txt"))
        else:
            click.echo(
                f"'{path}' is not a valid path to a requirements.txt file or directory"
            )

    exclusion_pattern = re.compile(r"(venv|\.venv|virtualenv|\.aws-sam)")
    filtered_requirements_files = [
        file for file in requirements_files if not exclusion_pattern.search(str(file))
    ]

    return filtered_requirements_files


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


def check_package_name(package_name: str, line: str) -> bool:
    """Determine if a line in a requirements.txt file contains the given package name"""

    if package_name == line:
        return True

    # If line is commented out, ignore it.
    if line.startswith("#"):
        return False

    # We make the package name and the line match in terms of dashes and underscores.
    if "-" in package_name:
        line = line.replace("_", "-")
    if "_" in package_name:
        line = line.replace("-", "_")

    # If the line is a package that is being referenced by a local path, we need to
    # check the last part of the path to see if it matches the package name.
    if line.startswith("./") or line.startswith("../"):
        return package_name in line.split("/")[-1]

    # Finally, we remove any sort of version specifier from the line and then check
    # if the package name matches.
    line = re.split(r"~=|==|>=|<=|>|<|!=", line)[0].strip()

    return package_name == line


@click.group(
    help="Manage requirements.txt files such as adding, removing, and updating individual packages in bulk"
)
@click.version_option(package_name="requirements")
def cli() -> None:
    pass


update_help = (
    "Replace a package name in requirements.txt files\n\nExample: "
    "requirements replace <package-name> <new-package-name> /path/to/requirements.txt"
)


@cli.command(name="update", help=update_help)
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
    """Replace a package name in requirements.txt files"""

    # If the version specifier does not start with ==, !=, >=, <=, >, <, or ~=,
    # default to ==.
    if not version_specifier.startswith(("==", "!=", ">=", "<=", ">", "<", "~=")):
        version_specifier = f"=={version_specifier}"

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text().splitlines()
        modified = False

        for index, line in enumerate(contents):
            if check_package_name(package_name, line):
                contents[index] = f"{package_name}{version_specifier}"
                modified = True
                contents = sort_packages(contents, locale_=DEFAULT_LOCALE)

        if modified:
            if preview:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(contents).strip() + "\n")
            else:
                if check_file_writable(requirements_file, preview):
                    requirements_file.write_text("\n".join(contents).strip() + "\n")
                    click.echo(f"Updated {requirements_file}")


find_help = (
    "Find a package name in requirements.txt files\n\nExample: "
    "requirements find <package-name> /path/to/requirements.txt"
)


@cli.command(name="find", help=find_help)
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print the package contained in the requirements.txt file",
)
def find_package(package_name: str, paths: tuple[str], verbose: bool) -> None:
    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        for line in requirements_file.read_text().splitlines():
            if check_package_name(package_name, line):
                click.echo(requirements_file)
                if verbose:
                    click.echo(line)


add_help = (
    "Add a package to requirements.txt files\n\nExample: "
    "requirements add <package-name> /path/to/requirements.txt"
)


@cli.command(name="add", help=add_help)
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def add_package(package_name: str, paths: tuple[str], preview: bool) -> None:
    """Add a package to requirements.txt files"""

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text().splitlines()
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
            else:
                if check_file_writable(requirements_file, preview):
                    requirements_file.write_text("\n".join(contents).strip() + "\n")
                    click.echo(f"Updated {requirements_file}")


remove_help = (
    "Remove a package from requirements.txt files\n\nExample: "
    "requirements remove <package-name> /path/to/requirements.txt"
)


@cli.command(name="remove", help=remove_help)
@click.argument("package_name")
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def remove_package(package_name: str, paths: tuple[str], preview: bool) -> None:
    """Remove a package from requirements.txt files"""

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text().splitlines()
        updated_contents = [
            line for line in contents if not check_package_name(package_name, line)
        ]
        updated_contents = sort_packages(updated_contents, locale_=DEFAULT_LOCALE)

        if preview:
            click.echo(click.style(requirements_file, fg="cyan", bold=True))
            click.echo("\n".join(updated_contents).strip() + "\n")

        if len(contents) != len(updated_contents) and not preview and check_file_writable(requirements_file, preview):
            requirements_file.write_text("\n".join(updated_contents) + "\n")
            click.echo(f"Removed {package_name} from {requirements_file}")


sort_help = (
    "Sort requirements.txt files in place\n\nExample: "
    "requirements sort /path/to/requirements.txt"
)


@cli.command(name="sort", help=sort_help)
@click.argument("paths", nargs=-1)
@click.option("--preview", is_flag=True, help="Preview file changes without saving")
def sort_requirements(paths: tuple[str], preview: bool) -> None:
    """Sort requirements.txt files in place"""

    if preview:
        click.echo("Previewing changes")

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        contents = requirements_file.read_text().splitlines()
        new_contents = sort_packages(contents, locale_=DEFAULT_LOCALE)
        if contents != new_contents:
            if not preview:
                if check_file_writable(requirements_file, preview):
                    requirements_file.write_text("\n".join(new_contents).strip() + "\n")
                    click.echo(f"Sorted {requirements_file}")
            else:
                click.echo(click.style(requirements_file, fg="cyan", bold=True))
                click.echo("\n".join(new_contents).strip() + "\n")
        else:
            click.echo(f"{requirements_file} is already sorted")


cat_help = (
    "Cat the contents of requirements.txt files\n\nExample: "
    "requirements cat /path/to/requirements.txt"
)


@cli.command(name="cat", help=cat_help)
@click.argument("paths", nargs=-1)
def cat_requirements(paths: tuple[str]) -> None:
    """Cat the contents of all requirements.txt files in a given path(s)"""

    resolved_paths = resolve_paths(paths)

    for requirements_file in gather_requirements_files(resolved_paths):
        click.echo(click.style(requirements_file, fg="cyan", bold=True))
        click.echo(requirements_file.read_text().strip())
        click.echo()


if __name__ == "__main__":
    cli()
